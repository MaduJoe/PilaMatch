import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models import User, UserRole
from app.schemas.contract import ContractResponse, ContractListResponse, ContractCancelRequest
from app.services.contract import ContractService
from app.services.contract_document import render_contract_html

logger = logging.getLogger(__name__)


class NoShowReportRequest(BaseModel):
    reported_user_id: str

router = APIRouter()


@router.post("/from-offer/{offer_id}", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract_from_offer(
    offer_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a contract from an accepted offer."""
    service = ContractService(db)

    try:
        contract = await service.create_from_offer(offer_id, current_user.id)
        return ContractResponse.model_validate(contract)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CONTRACT_FAILED", "message": str(e)},
        )


@router.get("/me", response_model=ContractListResponse)
async def get_my_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's contracts with profile names."""
    from app.models import InstructorProfile, StudioProfile
    from sqlalchemy import select

    service = ContractService(db)
    contracts, total = await service.get_by_user(
        current_user.id, current_user.role, skip=skip, limit=limit
    )

    # Batch-fetch profile names to avoid N+1
    instructor_ids = {c.instructor_id for c in contracts}
    studio_ids = {c.studio_id for c in contracts}

    instructor_names: dict = {}
    if instructor_ids:
        rows = await db.execute(
            select(InstructorProfile.id, InstructorProfile.display_name)
            .where(InstructorProfile.id.in_(instructor_ids))
        )
        instructor_names = {row[0]: row[1] for row in rows.all()}

    studio_names: dict = {}
    if studio_ids:
        rows = await db.execute(
            select(StudioProfile.id, StudioProfile.business_name)
            .where(StudioProfile.id.in_(studio_ids))
        )
        studio_names = {row[0]: row[1] for row in rows.all()}

    enriched_contracts = []
    for contract in contracts:
        contract_dict = {
            "id": contract.id,
            "offer_id": contract.offer_id,
            "studio_id": contract.studio_id,
            "instructor_id": contract.instructor_id,
            "status": contract.status,
            "hourly_rate": contract.hourly_rate,
            "total_amount": contract.total_amount,
            "total_sessions": contract.total_sessions,
            "date": contract.date,
            "start_time": contract.start_time,
            "end_time": contract.end_time,
            "instructor_signed_at": contract.instructor_signed_at,
            "studio_signed_at": contract.studio_signed_at,
            "studio_confirmed_at": contract.studio_confirmed_at,
            "instructor_confirmed_at": contract.instructor_confirmed_at,
            "platform_fee": contract.platform_fee,
            "settlement_amount": contract.settlement_amount,
            "recurring_days": contract.recurring_days,
            "recurring_end_date": contract.recurring_end_date,
            "cancellation_reason": contract.cancellation_reason,
            "cancelled_by_user_id": contract.cancelled_by_user_id,
            "created_at": contract.created_at,
            "updated_at": contract.updated_at,
            "instructor_name": instructor_names.get(contract.instructor_id),
            "studio_name": studio_names.get(contract.studio_id),
        }
        enriched_contracts.append(ContractResponse(**contract_dict))

    return ContractListResponse(
        items=enriched_contracts,
        total=total,
    )


@router.get("/{contract_id}/schedule")
async def get_contract_schedule(
    contract_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recurring schedule for a contract.

    Returns session dates, next session, and formatted weekday labels
    for contracts with a recurring schedule. For single-date contracts
    the response indicates is_recurring=False.

    Args:
        contract_id: The contract UUID to look up.
        current_user: The authenticated user (injected).
        db: Async database session (injected).

    Returns:
        Schedule details including all dates and the next upcoming session.
    """
    service = ContractService(db)
    contract = await service.get_by_id(contract_id)

    if not contract:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "계약을 찾을 수 없습니다"},
        )

    if not contract.recurring_days:
        return {
            "is_recurring": False,
            "dates": [str(contract.date)],
            "total_sessions": contract.total_sessions,
        }

    from app.services.recurring_schedule import (
        generate_recurring_dates,
        format_recurring_days_ko,
        get_next_session_date,
    )
    from datetime import date as date_type

    dates = generate_recurring_dates(
        contract.date,
        contract.recurring_end_date or contract.date,
        contract.recurring_days,
    )

    next_session = get_next_session_date(
        date_type.today(),
        contract.recurring_days,
        contract.recurring_end_date or contract.date,
    )

    return {
        "is_recurring": True,
        "recurring_days": contract.recurring_days,
        "recurring_days_label": format_recurring_days_ko(contract.recurring_days),
        "start_date": str(contract.date),
        "end_date": str(contract.recurring_end_date) if contract.recurring_end_date else None,
        "dates": [str(d) for d in dates],
        "total_sessions": len(dates),
        "next_session": str(next_session) if next_session else None,
        "start_time": str(contract.start_time) if contract.start_time else None,
        "end_time": str(contract.end_time) if contract.end_time else None,
    }


@router.get("/{contract_id}/document", response_class=HTMLResponse)
async def get_contract_document(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HTMLResponse:
    """계약서 문서를 HTML로 반환한다.

    브라우저에서 Ctrl+P (Cmd+P)로 PDF 인쇄/저장이 가능하다.
    계약 당사자(스튜디오 또는 강사)만 조회할 수 있다.

    Args:
        contract_id: 조회할 계약 ID.
        db: 비동기 DB 세션.
        current_user: 인증된 사용자.

    Returns:
        HTML 계약서 문서.
    """
    service = ContractService(db)

    try:
        data = await service.get_contract_document_data(
            contract_id, current_user.id
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "CONTRACT_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CONTRACT_NOT_FOUND", "message": "계약을 찾을 수 없습니다"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "DOCUMENT_FAILED", "message": error_msg},
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "계약 당사자만 계약서를 조회할 수 있습니다",
            },
        )

    html_content = render_contract_html(data)

    logger.info(
        "계약서 문서 반환: contract_id=%s, user_id=%s",
        contract_id,
        current_user.id,
    )

    return HTMLResponse(content=html_content, status_code=200)


@router.post("/{contract_id}/set-in-progress", response_model=ContractResponse)
async def set_contract_in_progress(
    contract_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set contract status to in progress (both parties can sign)."""
    service = ContractService(db)

    # Get profile ID based on role
    if current_user.role == UserRole.STUDIO.value:
        profile_id = await service.get_studio_profile_id(current_user.id)
    else:
        profile_id = await service.get_instructor_profile_id(current_user.id)

    if not profile_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Profile not found"},
        )

    try:
        contract = await service.set_in_progress(
            contract_id, current_user.id, profile_id, current_user.role
        )
        return ContractResponse.model_validate(contract)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to update this contract"},
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "INVALID_STATE_TRANSITION":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_STATE_TRANSITION", "message": "Invalid state transition"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UPDATE_FAILED", "message": error_msg},
        )


@router.post("/{contract_id}/confirm-completion", response_model=ContractResponse)
async def confirm_contract_completion(
    contract_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirm contract completion (v2.0 - bidirectional confirmation required)."""
    service = ContractService(db)

    if current_user.role == UserRole.STUDIO.value:
        profile_id = await service.get_studio_profile_id(current_user.id)
    else:
        profile_id = await service.get_instructor_profile_id(current_user.id)

    if not profile_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Profile not found"},
        )

    try:
        contract = await service.confirm_completion(
            contract_id, current_user.id, profile_id, current_user.role
        )
        return ContractResponse.model_validate(contract)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to confirm this contract"},
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "CONTRACT_NOT_IN_PROGRESS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "CONTRACT_NOT_IN_PROGRESS", "message": "Contract must be in progress to confirm completion"},
            )
        if error_msg.startswith("Already confirmed"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ALREADY_CONFIRMED", "message": error_msg},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CONFIRM_FAILED", "message": error_msg},
        )


class RejectCompletionRequest(BaseModel):
    reason: str


@router.post("/{contract_id}/reject-completion", response_model=ContractResponse)
async def reject_contract_completion(
    contract_id: UUID,
    data: RejectCompletionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject contract completion and create a dispute (v2.0)."""
    service = ContractService(db)

    if current_user.role == UserRole.STUDIO.value:
        profile_id = await service.get_studio_profile_id(current_user.id)
    else:
        profile_id = await service.get_instructor_profile_id(current_user.id)

    if not profile_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Profile not found"},
        )

    try:
        contract = await service.reject_completion(
            contract_id, current_user.id, profile_id, current_user.role, data.reason
        )
        return ContractResponse.model_validate(contract)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to reject this contract"},
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "CONTRACT_NOT_PENDING_COMPLETION":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "CONTRACT_NOT_PENDING", "message": "Contract must be pending completion to reject"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "REJECT_FAILED", "message": error_msg},
        )


@router.post("/{contract_id}/cancel", response_model=ContractResponse)
async def cancel_contract(
    contract_id: UUID,
    data: ContractCancelRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a contract (requires reason)."""
    service = ContractService(db)

    if current_user.role == UserRole.STUDIO.value:
        profile_id = await service.get_studio_profile_id(current_user.id)
    else:
        profile_id = await service.get_instructor_profile_id(current_user.id)

    if not profile_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Profile not found"},
        )

    try:
        contract = await service.cancel(
            contract_id, current_user.id, profile_id, current_user.role, data.reason
        )
        return ContractResponse.model_validate(contract)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to cancel this contract"},
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "CANCEL_REASON_REQUIRED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "CANCEL_REASON_REQUIRED", "message": "Cancellation reason is required"},
            )
        if error_msg == "INVALID_STATE_TRANSITION":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_STATE_TRANSITION", "message": "Cannot cancel contract in this state"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CANCEL_FAILED", "message": error_msg},
        )


class NoShowDisputeResponse(BaseModel):
    dispute_id: str
    objection_deadline: str
    message: str


@router.post("/{contract_id}/report-no-show", response_model=NoShowDisputeResponse)
async def report_contract_no_show(
    contract_id: UUID,
    data: NoShowReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Report a no-show for a contract (v2.0 - creates a dispute with 24h objection period)."""
    service = ContractService(db)

    # Verify contract exists and user is part of it
    contract = await service.get_by_id(contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CONTRACT_NOT_FOUND", "message": "Contract not found"},
        )

    # Only allow reporting after contract date has passed
    # and contract is still in confirmed or in_progress state
    from app.models.enums import ContractStatus
    if contract.status not in [ContractStatus.CONFIRMED.value, ContractStatus.IN_PROGRESS.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_CONTRACT_STATE", "message": "Can only report no-show for active contracts"},
        )

    # Get profile ID for authorization check
    if current_user.role == UserRole.STUDIO.value:
        profile_id = await service.get_studio_profile_id(current_user.id)
    else:
        profile_id = await service.get_instructor_profile_id(current_user.id)

    if not profile_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Profile not found"},
        )

    # BOLA check: verify user is a party to this contract
    if str(profile_id) != str(contract.studio_id) and str(profile_id) != str(contract.instructor_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to report no-show for this contract"},
        )

    try:
        # Create a no-show dispute instead of immediate penalty (v2.0)
        from app.services.dispute import DisputeService
        from uuid import UUID as UUID_Type

        # Convert profile ID to user ID
        # The frontend sends profile IDs (instructor_id or studio_id from contract)
        # But we need user IDs for the dispute
        reported_profile_id = UUID_Type(data.reported_user_id)

        # Get the user ID from the profile ID
        if current_user.role == UserRole.STUDIO.value:
            # Studio is reporting instructor - get instructor's user ID
            from sqlalchemy import select
            from app.models import InstructorProfile
            result = await db.execute(
                select(InstructorProfile.user_id).where(InstructorProfile.id == reported_profile_id)
            )
            reported_user_id = result.scalar_one_or_none()
            if not reported_user_id:
                raise ValueError("Instructor profile not found")
        else:
            # Instructor is reporting studio - get studio's user ID
            from sqlalchemy import select
            from app.models import StudioProfile
            result = await db.execute(
                select(StudioProfile.user_id).where(StudioProfile.id == reported_profile_id)
            )
            reported_user_id = result.scalar_one_or_none()
            if not reported_user_id:
                raise ValueError("Studio profile not found")

        dispute_service = DisputeService(db)
        dispute = await dispute_service.create_no_show_dispute(
            contract_id=contract_id,
            reporter_id=current_user.id,
            reported_user_id=reported_user_id,
        )

        # Cancel the contract due to no-show report
        # profile_id already resolved from the authorization check above
        await service.cancel(
            contract_id, current_user.id, profile_id, current_user.role,
            reason=f"No-show reported by {current_user.role}"
        )

        message = (
            "No-show reported. The other party has 24 hours to object. "
            "If no objection is received, the penalty will be automatically applied."
        )

        return NoShowDisputeResponse(
            dispute_id=str(dispute.id),
            objection_deadline=dispute.objection_deadline.isoformat() if dispute.objection_deadline else "",
            message=message,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "REPORT_FAILED", "message": str(e)},
        )
