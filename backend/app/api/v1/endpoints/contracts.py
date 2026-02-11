from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models import User, UserRole
from app.schemas.contract import ContractResponse, ContractListResponse, ContractCancelRequest
from app.services.contract import ContractService
from app.services.penalty import report_no_show, get_user_penalty_status


class NoShowReportRequest(BaseModel):
    reported_user_id: str


class NoShowReportResponse(BaseModel):
    no_show_count: int
    is_suspended: bool
    remaining_chances: int
    message: str

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
    """Get current user's contracts."""
    service = ContractService(db)
    contracts = await service.get_by_user(current_user.id, current_user.role)

    return ContractListResponse(
        items=[ContractResponse.model_validate(c) for c in contracts],
        total=len(contracts),
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


@router.post("/{contract_id}/complete", response_model=ContractResponse)
async def complete_contract(
    contract_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark contract as completed."""
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
        contract = await service.complete(
            contract_id, current_user.id, profile_id, current_user.role
        )
        return ContractResponse.model_validate(contract)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to complete this contract"},
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "CONTRACT_NOT_IN_PROGRESS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "CONTRACT_NOT_IN_PROGRESS", "message": "Contract must be in progress to complete"},
            )
        if error_msg == "INVALID_STATE_TRANSITION":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_STATE_TRANSITION", "message": "Invalid state transition"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "COMPLETE_FAILED", "message": error_msg},
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


@router.post("/{contract_id}/report-no-show", response_model=NoShowReportResponse)
async def report_contract_no_show(
    contract_id: UUID,
    data: NoShowReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Report a no-show for a contract. After 3 no-shows, user is suspended."""
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
        result = await report_no_show(
            db=db,
            contract_id=str(contract_id),
            reported_user_id=data.reported_user_id,
            reporter_user_id=str(current_user.id),
        )

        # Also cancel the contract due to no-show
        if current_user.role == UserRole.STUDIO.value:
            profile_id = await service.get_studio_profile_id(current_user.id)
        else:
            profile_id = await service.get_instructor_profile_id(current_user.id)

        await service.cancel(
            contract_id, current_user.id, profile_id, current_user.role,
            reason=f"No-show reported by {current_user.role}"
        )

        message = "No-show reported successfully."
        if result["is_suspended"]:
            message = "No-show reported. User has been suspended due to repeated no-shows."

        return NoShowReportResponse(
            no_show_count=result["no_show_count"],
            is_suspended=result["is_suspended"],
            remaining_chances=result["remaining_chances"],
            message=message,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "REPORT_FAILED", "message": str(e)},
        )
