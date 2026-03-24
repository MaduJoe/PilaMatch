"""Handoff template endpoints -- reusable handoff note templates and feedback."""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_role
from app.models import User, UserRole, HandoffNote, Application
from app.models.instructor import InstructorProfile
from app.services.handoff_template import HandoffTemplateService

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Schemas ---


class HandoffTemplateCreateRequest(BaseModel):
    name: str
    class_topic: Optional[str] = None
    class_sequence_info: Optional[str] = None
    atmosphere_preference: Optional[str] = None
    member_caution_tags: Optional[list[str]] = None
    member_free_text: Optional[str] = None
    equipment_notes: Optional[str] = None
    additional_notes: Optional[str] = None


class HandoffTemplateUpdateRequest(BaseModel):
    name: Optional[str] = None
    class_topic: Optional[str] = None
    class_sequence_info: Optional[str] = None
    atmosphere_preference: Optional[str] = None
    member_caution_tags: Optional[list[str]] = None
    member_free_text: Optional[str] = None
    equipment_notes: Optional[str] = None
    additional_notes: Optional[str] = None


class HandoffTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    studio_id: str
    name: str
    class_topic: Optional[str] = None
    class_sequence_info: Optional[str] = None
    atmosphere_preference: Optional[str] = None
    member_caution_tags: Optional[list[str]] = None
    member_free_text: Optional[str] = None
    equipment_notes: Optional[str] = None
    additional_notes: Optional[str] = None
    usage_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class HandoffNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_post_id: str
    class_topic: Optional[str] = None
    class_sequence_info: Optional[str] = None
    atmosphere_preference: Optional[str] = None
    member_caution_tags: Optional[list[str]] = None
    member_free_text: Optional[str] = None
    equipment_notes: Optional[str] = None
    additional_notes: Optional[str] = None
    completeness_score: Optional[float] = None
    template_id: Optional[str] = None


class HandoffFeedbackRequest(BaseModel):
    feedback: str


class HandoffFeedbackResponse(BaseModel):
    status: str
    instructor_feedback: str


# --- Helpers ---


def _template_to_response(template) -> HandoffTemplateResponse:
    """Convert a HandoffTemplate ORM model to response schema."""
    return HandoffTemplateResponse(
        id=str(template.id),
        studio_id=str(template.studio_id),
        name=template.name,
        class_topic=template.class_topic,
        class_sequence_info=template.class_sequence_info,
        atmosphere_preference=template.atmosphere_preference,
        member_caution_tags=template.member_caution_tags,
        member_free_text=template.member_free_text,
        equipment_notes=template.equipment_notes,
        additional_notes=template.additional_notes,
        usage_count=template.usage_count or 0,
        created_at=template.created_at.isoformat() if template.created_at else None,
        updated_at=template.updated_at.isoformat() if template.updated_at else None,
    )


def _note_to_response(note: HandoffNote) -> HandoffNoteResponse:
    """Convert a HandoffNote ORM model to response schema."""
    return HandoffNoteResponse(
        id=str(note.id),
        job_post_id=str(note.job_post_id),
        class_topic=note.class_topic,
        class_sequence_info=note.class_sequence_info,
        atmosphere_preference=note.atmosphere_preference,
        member_caution_tags=note.member_caution_tags,
        member_free_text=note.member_free_text,
        equipment_notes=note.equipment_notes,
        additional_notes=note.additional_notes,
        completeness_score=float(note.completeness_score) if note.completeness_score else None,
        template_id=str(note.template_id) if note.template_id else None,
    )


# --- Template CRUD Endpoints ---


@router.post(
    "/studios/me/handoff-templates",
    response_model=HandoffTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_handoff_template(
    body: HandoffTemplateCreateRequest,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new handoff template for the studio."""
    service = HandoffTemplateService(db)

    try:
        template = await service.create_template(
            user_id=str(current_user.id),
            name=body.name,
            class_topic=body.class_topic,
            class_sequence_info=body.class_sequence_info,
            atmosphere_preference=body.atmosphere_preference,
            member_caution_tags=body.member_caution_tags,
            member_free_text=body.member_free_text,
            equipment_notes=body.equipment_notes,
            additional_notes=body.additional_notes,
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "STUDIO_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "STUDIO_NOT_FOUND", "message": "Studio profile not found"},
            )
        if error_msg == "TEMPLATE_LIMIT_REACHED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "TEMPLATE_LIMIT_REACHED", "message": "Maximum 20 templates per studio"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "TEMPLATE_FAILED", "message": error_msg},
        )

    await db.commit()

    return _template_to_response(template)


@router.get("/studios/me/handoff-templates", response_model=list[HandoffTemplateResponse])
async def list_handoff_templates(
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """List all handoff templates for the current studio."""
    service = HandoffTemplateService(db)

    try:
        templates = await service.list_templates(user_id=str(current_user.id))
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "STUDIO_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "STUDIO_NOT_FOUND", "message": "Studio profile not found"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "LIST_FAILED", "message": error_msg},
        )

    return [_template_to_response(t) for t in templates]


@router.put("/studios/me/handoff-templates/{template_id}", response_model=HandoffTemplateResponse)
async def update_handoff_template(
    template_id: UUID,
    body: HandoffTemplateUpdateRequest,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing handoff template."""
    service = HandoffTemplateService(db)

    update_data = body.model_dump(exclude_unset=True)

    try:
        template = await service.update_template(
            user_id=str(current_user.id),
            template_id=str(template_id),
            **update_data,
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "TEMPLATE_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "TEMPLATE_NOT_FOUND", "message": "Template not found or not owned by this studio"},
            )
        if error_msg == "STUDIO_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "STUDIO_NOT_FOUND", "message": "Studio profile not found"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UPDATE_FAILED", "message": error_msg},
        )

    await db.commit()

    return _template_to_response(template)


@router.delete("/studios/me/handoff-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_handoff_template(
    template_id: UUID,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a handoff template."""
    service = HandoffTemplateService(db)

    try:
        await service.delete_template(
            user_id=str(current_user.id),
            template_id=str(template_id),
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "TEMPLATE_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "TEMPLATE_NOT_FOUND", "message": "Template not found or not owned by this studio"},
            )
        if error_msg == "STUDIO_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "STUDIO_NOT_FOUND", "message": "Studio profile not found"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "DELETE_FAILED", "message": error_msg},
        )

    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Template Application Endpoint ---


@router.post(
    "/job-posts/{job_post_id}/handoff-note/from-template/{template_id}",
    response_model=HandoffNoteResponse,
)
async def apply_template_to_handoff(
    job_post_id: UUID,
    template_id: UUID,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """Apply a handoff template to a job post's handoff note.

    Copies template fields to the handoff note and increments usage count.
    """
    service = HandoffTemplateService(db)

    try:
        note = await service.apply_template(
            user_id=str(current_user.id),
            template_id=str(template_id),
            job_post_id=str(job_post_id),
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "TEMPLATE_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "TEMPLATE_NOT_FOUND", "message": "Template not found or not owned by this studio"},
            )
        if error_msg == "HANDOFF_NOTE_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "HANDOFF_NOTE_NOT_FOUND", "message": "Handoff note not found for this job post"},
            )
        if error_msg == "STUDIO_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "STUDIO_NOT_FOUND", "message": "Studio profile not found"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "APPLY_FAILED", "message": error_msg},
        )

    await db.commit()

    return _note_to_response(note)


# --- Instructor Feedback Endpoint ---


@router.post(
    "/job-posts/{job_post_id}/handoff-note/feedback",
    response_model=HandoffFeedbackResponse,
)
async def submit_handoff_feedback(
    job_post_id: UUID,
    body: HandoffFeedbackRequest,
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Submit instructor feedback on a handoff note after completing a lesson.

    The instructor must have an accepted application for this job.
    """
    # Load handoff note
    note_result = await db.execute(
        select(HandoffNote).where(HandoffNote.job_post_id == str(job_post_id))
    )
    note = note_result.scalar_one_or_none()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "HANDOFF_NOTE_NOT_FOUND", "message": "Handoff note not found for this job post"},
        )

    # Verify instructor has an accepted application for this job
    profile_result = await db.execute(
        select(InstructorProfile).where(InstructorProfile.user_id == current_user.id)
    )
    instructor = profile_result.scalar_one_or_none()
    if not instructor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Instructor profile not found"},
        )

    app_result = await db.execute(
        select(Application).where(
            and_(
                Application.job_post_id == str(job_post_id),
                Application.instructor_id == instructor.id,
                Application.status == "accepted",
            )
        )
    )
    application = app_result.scalar_one_or_none()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "No accepted application found for this job"},
        )

    # Update feedback
    note.instructor_feedback = body.feedback
    note.instructor_feedback_at = datetime.utcnow()

    await db.commit()

    return HandoffFeedbackResponse(
        status="ok",
        instructor_feedback=note.instructor_feedback,
    )
