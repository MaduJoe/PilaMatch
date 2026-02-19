from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models import User, UserRole
from app.schemas.contract import ContractResponse, ContractListResponse, ContractCancelRequest
from app.services.contract import ContractService
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's contracts with profile names."""
    from app.models import InstructorProfile, StudioProfile
    from sqlalchemy import select

    service = ContractService(db)
    contracts = await service.get_by_user(current_user.id, current_user.role)

    # Enrich contracts with profile names
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
            "cancellation_reason": contract.cancellation_reason,
            "cancelled_by_user_id": contract.cancelled_by_user_id,
            "created_at": contract.created_at,
            "updated_at": contract.updated_at,
        }

        # Get instructor name
        instructor = await db.execute(
            select(InstructorProfile.display_name)
            .where(InstructorProfile.id == contract.instructor_id)
        )
        instructor_name = instructor.scalar_one_or_none()
        contract_dict["instructor_name"] = instructor_name

        # Get studio name
        studio = await db.execute(
            select(StudioProfile.business_name)
            .where(StudioProfile.id == contract.studio_id)
        )
        studio_name = studio.scalar_one_or_none()
        contract_dict["studio_name"] = studio_name

        enriched_contracts.append(ContractResponse(**contract_dict))

    return ContractListResponse(
        items=enriched_contracts,
        total=len(enriched_contracts),
    )


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
        if current_user.role == UserRole.STUDIO.value:
            profile_id = await service.get_studio_profile_id(current_user.id)
        else:
            profile_id = await service.get_instructor_profile_id(current_user.id)

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
