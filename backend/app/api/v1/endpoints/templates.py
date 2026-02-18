"""Application template endpoints (v3.0 Phase 2 - Premium feature)."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User
from app.services.application_template import ApplicationTemplateService
from app.services.subscription import SubscriptionService


# Schemas
class TemplateCreate(BaseModel):
    name: str
    content: str
    is_default: bool = False


class TemplateUpdate(BaseModel):
    name: str = None
    content: str = None
    is_default: bool = None


class TemplateResponse(BaseModel):
    id: str
    name: str
    content: str
    is_default: bool
    usage_count: int
    created_at: str


class TemplateSuggestion(BaseModel):
    name: str
    content: str


router = APIRouter()


@router.get("/application-templates", response_model=List[TemplateResponse])
async def get_my_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all application templates for current user (Premium feature)."""
    service = ApplicationTemplateService(db)
    templates = await service.get_user_templates(current_user.id)

    return [
        TemplateResponse(
            id=str(t.id),
            name=t.name,
            content=t.content,
            is_default=t.is_default,
            usage_count=t.usage_count,
            created_at=t.created_at.isoformat(),
        )
        for t in templates
    ]


@router.post("/application-templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new application template (Premium only)."""
    service = ApplicationTemplateService(db)

    try:
        template = await service.create_template(
            user_id=current_user.id,
            name=data.name,
            content=data.content,
            is_default=data.is_default,
        )
    except ValueError as e:
        error_msg = str(e)
        if "PREMIUM_REQUIRED" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "PREMIUM_REQUIRED", "message": error_msg.split(":", 1)[1]},
            )
        elif "TEMPLATE_LIMIT" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "TEMPLATE_LIMIT", "message": error_msg.split(":", 1)[1]},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ERROR", "message": error_msg},
            )

    return TemplateResponse(
        id=str(template.id),
        name=template.name,
        content=template.content,
        is_default=template.is_default,
        usage_count=template.usage_count,
        created_at=template.created_at.isoformat(),
    )


@router.put("/application-templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing template."""
    service = ApplicationTemplateService(db)

    template = await service.update_template(
        template_id=template_id,
        user_id=current_user.id,
        name=data.name,
        content=data.content,
        is_default=data.is_default,
    )

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TEMPLATE_NOT_FOUND", "message": "Template not found"},
        )

    return TemplateResponse(
        id=str(template.id),
        name=template.name,
        content=template.content,
        is_default=template.is_default,
        usage_count=template.usage_count,
        created_at=template.created_at.isoformat(),
    )


@router.delete("/application-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a template."""
    service = ApplicationTemplateService(db)

    success = await service.delete_template(template_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TEMPLATE_NOT_FOUND", "message": "Template not found"},
        )


@router.get("/application-templates/suggestions", response_model=List[TemplateSuggestion])
async def get_template_suggestions(
    job_type: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get template suggestions based on job type (Premium feature)."""
    service = ApplicationTemplateService(db)
    suggestions = await service.get_template_suggestions(current_user.id, job_type)

    return [TemplateSuggestion(**s) for s in suggestions]


@router.post("/application-templates/{template_id}/use")
async def use_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Use a template (increments usage count and returns content)."""
    service = ApplicationTemplateService(db)
    content = await service.use_template(template_id, current_user.id)

    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TEMPLATE_NOT_FOUND", "message": "Template not found"},
        )

    return {"content": content}