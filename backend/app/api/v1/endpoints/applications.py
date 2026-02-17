from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_role
from app.models import User, UserRole
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationWithJobResponse,
    ApplicationListResponse,
    ApplicationWithInstructorResponse,
    ApplicationWithInstructorListResponse,
)
from app.services.application import ApplicationService

router = APIRouter()


@router.post(
    "/job-posts/{job_post_id}/applications",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_application(
    job_post_id: UUID,
    data: ApplicationCreate,
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Apply to a job post (instructor only)."""
    service = ApplicationService(db)
    instructor_id = await service.get_instructor_profile_id(current_user.id)

    if not instructor_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Instructor profile not found"},
        )

    try:
        application = await service.create(job_post_id, instructor_id, data)
        return ApplicationResponse.model_validate(application)
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "DUPLICATE_APPLICATION":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "DUPLICATE_APPLICATION", "message": "Already applied to this job post"},
            )
        elif error_msg == "INSUFFICIENT_DEPOSIT":
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={"code": "INSUFFICIENT_DEPOSIT", "message": "Deposit required to apply for jobs"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "APPLICATION_FAILED", "message": error_msg},
        )


@router.get(
    "/job-posts/{job_post_id}/applications",
    response_model=ApplicationWithInstructorListResponse,
)
async def get_job_post_applications(
    job_post_id: UUID,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """Get all applications for a job post (studio owner only)."""
    service = ApplicationService(db)
    studio_id = await service.get_studio_profile_id(current_user.id)

    if not studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Studio profile not found"},
        )

    try:
        results = await service.get_by_job_post(job_post_id, studio_id)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to view applications for this job post"},
        )

    items = []
    for application, instructor, has_offer in results:
        item = ApplicationWithInstructorResponse(
            id=application.id,
            job_post_id=application.job_post_id,
            instructor_id=application.instructor_id,
            status=application.status,
            cover_letter=application.cover_letter,
            created_at=application.created_at,
            updated_at=application.updated_at,
            instructor_name=instructor.display_name,
            instructor_phone=instructor.phone,
            instructor_experience_years=instructor.experience_years,
            instructor_categories=instructor.categories,
            instructor_rating=float(instructor.rating_average) if instructor.rating_average else None,
            has_offer=has_offer,
        )
        items.append(item)

    return ApplicationWithInstructorListResponse(items=items, total=len(items))


@router.get("/applications/me", response_model=ApplicationListResponse)
async def get_my_applications(
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Get current instructor's applications."""
    service = ApplicationService(db)
    instructor_id = await service.get_instructor_profile_id(current_user.id)

    if not instructor_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Instructor profile not found"},
        )

    results = await service.get_by_instructor(instructor_id)

    items = []
    for application, job_title, studio_name in results:
        item = ApplicationWithJobResponse(
            id=application.id,
            job_post_id=application.job_post_id,
            instructor_id=application.instructor_id,
            status=application.status,
            cover_letter=application.cover_letter,
            created_at=application.created_at,
            updated_at=application.updated_at,
            job_title=job_title,
            studio_name=studio_name,
        )
        items.append(item)

    return ApplicationListResponse(items=items, total=len(items))


@router.post("/applications/{application_id}/withdraw", response_model=ApplicationResponse)
async def withdraw_application(
    application_id: UUID,
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Withdraw an application (instructor only)."""
    service = ApplicationService(db)
    instructor_id = await service.get_instructor_profile_id(current_user.id)

    if not instructor_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Instructor profile not found"},
        )

    try:
        application = await service.withdraw(application_id, instructor_id)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to withdraw this application"},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "WITHDRAW_FAILED", "message": str(e)},
        )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "APPLICATION_NOT_FOUND", "message": "Application not found"},
        )

    return ApplicationResponse.model_validate(application)
