from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.deps import require_role
from app.models import User, UserRole, InstructorProfile, StudioProfile, JobPost, ApplicationStatus
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationWithJobResponse,
    ApplicationListResponse,
    ApplicationWithInstructorResponse,
    ApplicationWithInstructorListResponse,
    ContactRevealResponse,
)
from app.services.application import ApplicationService
from app.utils.masking import mask_phone

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
        # v3.0: Profile completeness check replaces deposit check
        elif error_msg.startswith("INCOMPLETE_PROFILE:"):
            reason = error_msg.split(":", 1)[1] if ":" in error_msg else "프로필을 완성해주세요"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INCOMPLETE_PROFILE", "message": reason},
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
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
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
        results, total = await service.get_by_job_post(
            job_post_id, studio_id, skip=skip, limit=limit
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to view applications for this job post"},
        )

    items = []

    for application, instructor, has_offer in results:
        # Get no-show count from user model
        user_result = await db.execute(
            select(User).where(User.id == instructor.user_id)
        )
        inst_user = user_result.scalar_one_or_none()

        # Show full phone if contact is revealed, masked otherwise
        revealed = getattr(application, "contact_revealed", False)
        phone_display = instructor.phone if revealed else mask_phone(instructor.phone)

        item = ApplicationWithInstructorResponse(
            id=application.id,
            job_post_id=application.job_post_id,
            instructor_id=application.instructor_id,
            status=application.status,
            cover_letter=application.cover_letter,
            created_at=application.created_at,
            updated_at=application.updated_at,
            instructor_name=instructor.display_name,
            instructor_phone=phone_display,
            instructor_experience_years=instructor.experience_years,
            instructor_categories=instructor.categories,
            instructor_rating=float(instructor.rating_average) if instructor.rating_average else None,
            has_offer=has_offer,
            is_premium=False,  # PMF pivot: premium hidden
            contact_revealed=revealed,
            # Trust-tech profile data
            instructor_completed_substitutes=getattr(instructor, "completed_substitute_count", 0) or 0,
            instructor_no_show_count=inst_user.no_show_count if inst_user else 0,
            instructor_review_count=instructor.review_count or 0,
        )
        items.append(item)

    return ApplicationWithInstructorListResponse(items=items, total=total)


@router.get("/applications/me", response_model=ApplicationListResponse)
async def get_my_applications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
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

    results, total = await service.get_by_instructor(
        instructor_id, skip=skip, limit=limit
    )

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

    return ApplicationListResponse(items=items, total=total)


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


@router.post(
    "/applications/{application_id}/accept",
    response_model=ContactRevealResponse,
)
async def accept_application(
    application_id: UUID,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """Accept an application and reveal contact info to both parties.

    PMF pivot: Replaces the offer→contract flow with direct contact reveal.
    Studio accepts → both parties' phone numbers are immediately shared.
    """
    service = ApplicationService(db)
    studio_id = await service.get_studio_profile_id(current_user.id)

    if not studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Studio profile not found"},
        )

    # Get the application
    application = await service.get_by_id(application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "APPLICATION_NOT_FOUND", "message": "Application not found"},
        )

    # Verify job post belongs to this studio
    job_result = await db.execute(
        select(JobPost).where(
            JobPost.id == application.job_post_id,
            JobPost.studio_id == studio_id,
        )
    )
    job_post = job_result.scalar_one_or_none()
    if not job_post:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to accept this application"},
        )

    if application.status != ApplicationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_STATUS", "message": f"Cannot accept application with status '{application.status}'"},
        )

    # Accept the application and reveal contact info
    application.status = ApplicationStatus.ACCEPTED
    application.contact_revealed = True
    application.contact_revealed_at = datetime.utcnow()

    # Reject other pending applications for this job
    from app.models import Application
    other_result = await db.execute(
        select(Application).where(
            Application.job_post_id == application.job_post_id,
            Application.id != application.id,
            Application.status == ApplicationStatus.PENDING,
        )
    )
    for other_app in other_result.scalars().all():
        other_app.status = ApplicationStatus.REJECTED

    # Mark job as filled
    job_post.status = "filled"

    await db.commit()
    await db.refresh(application)

    # Get full contact info for both parties
    instructor_result = await db.execute(
        select(InstructorProfile).where(InstructorProfile.id == application.instructor_id)
    )
    instructor = instructor_result.scalar_one_or_none()

    studio_result = await db.execute(
        select(StudioProfile).where(StudioProfile.id == studio_id)
    )
    studio = studio_result.scalar_one_or_none()

    # Send notification to instructor
    try:
        from app.services.notification import NotificationService, NotificationType
        notif_service = NotificationService(db)
        await notif_service.send(
            user_id=str(instructor.user_id) if instructor else "",
            type=NotificationType.NEW_APPLICATION,
            title="지원이 수락되었습니다!",
            body=f"{studio.business_name if studio else '스튜디오'}에서 대타 지원을 수락했습니다. 연락처를 확인하세요.",
            data={
                "type": "application_accepted",
                "application_id": str(application_id),
                "studio_phone": studio.phone if studio else None,
            },
        )
    except Exception:
        pass  # Notification failure should not block

    # Record event
    try:
        from app.services.event_log import EventLogService
        event_service = EventLogService(db)
        await event_service.log(
            event_type="application.accepted_contact_revealed",
            actor_user_id=str(current_user.id),
            target_type="application",
            target_id=str(application_id),
            data={
                "job_post_id": str(job_post.id),
                "instructor_id": str(application.instructor_id),
            },
        )
        await db.commit()
    except Exception:
        pass

    return ContactRevealResponse(
        application_id=application.id,
        instructor_phone=instructor.phone or "등록된 번호 없음",
        instructor_name=instructor.display_name if instructor else "강사",
        studio_phone=studio.phone or "등록된 번호 없음",
        studio_name=studio.business_name if studio else "스튜디오",
        studio_address=studio.address if studio else None,
    )
