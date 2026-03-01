"""Backup Instructors API -- studio's trusted substitute pool management."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.deps import require_role
from app.models import User, UserRole, StudioProfile
from app.schemas.backup_instructor import (
    BackupInstructorCreate,
    BackupInstructorUpdate,
    BackupInstructorResponse,
    BackupInstructorListResponse,
)
from app.services.backup_instructor import BackupInstructorService

router = APIRouter()


async def _get_studio_id(user: User, db: AsyncSession) -> UUID:
    """Resolve the studio profile ID for the authenticated user.

    Args:
        user: Authenticated user model.
        db: Async database session.

    Returns:
        The studio profile UUID.

    Raises:
        HTTPException: 404 if no studio profile exists for the user.
    """
    result = await db.execute(
        select(StudioProfile.id).where(StudioProfile.user_id == user.id)
    )
    studio_id = result.scalar_one_or_none()
    if not studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Studio profile not found"},
        )
    return studio_id


@router.get("", response_model=BackupInstructorListResponse)
async def list_backup_instructors(
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
) -> BackupInstructorListResponse:
    """List all instructors in the studio's backup network.

    Returns:
        BackupInstructorListResponse with items and total count.
    """
    studio_id = await _get_studio_id(current_user, db)
    service = BackupInstructorService(db)
    results = await service.list_by_studio(studio_id)

    items = []
    for backup, instructor in results:
        items.append(BackupInstructorResponse(
            id=backup.id,
            studio_id=backup.studio_id,
            instructor_id=backup.instructor_id,
            nickname=backup.nickname,
            note=backup.note,
            priority=backup.priority,
            last_worked_at=backup.last_worked_at,
            total_completed=backup.total_completed,
            instructor_name=instructor.display_name,
            instructor_phone=instructor.phone,
            instructor_categories=instructor.categories,
            instructor_rating=float(instructor.rating_average) if instructor.rating_average else None,
            created_at=backup.created_at,
            updated_at=backup.updated_at,
        ))

    return BackupInstructorListResponse(items=items, total=len(items))


@router.post("", response_model=BackupInstructorResponse, status_code=status.HTTP_201_CREATED)
async def add_backup_instructor(
    data: BackupInstructorCreate,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
) -> BackupInstructorResponse:
    """Add an instructor to the studio's backup network.

    Args:
        data: BackupInstructorCreate with instructor_id and optional metadata.

    Returns:
        The newly created BackupInstructorResponse.

    Raises:
        HTTPException: 404 if instructor not found, 409 if already in backup.
    """
    studio_id = await _get_studio_id(current_user, db)
    service = BackupInstructorService(db)

    try:
        backup = await service.add(studio_id, data)
    except ValueError as e:
        msg = str(e)
        if msg == "INSTRUCTOR_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail={"code": "INSTRUCTOR_NOT_FOUND", "message": "Instructor not found"},
            )
        if msg == "ALREADY_IN_BACKUP":
            raise HTTPException(
                status_code=409,
                detail={"code": "ALREADY_IN_BACKUP", "message": "Instructor already in backup network"},
            )
        raise HTTPException(
            status_code=400,
            detail={"code": "ADD_FAILED", "message": msg},
        )

    return BackupInstructorResponse.model_validate(backup)


@router.patch("/{instructor_id}", response_model=BackupInstructorResponse)
async def update_backup_instructor(
    instructor_id: UUID,
    data: BackupInstructorUpdate,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
) -> BackupInstructorResponse:
    """Update a backup instructor entry (nickname, note, priority).

    Args:
        instructor_id: The instructor's profile UUID.
        data: BackupInstructorUpdate with optional fields.

    Returns:
        Updated BackupInstructorResponse.

    Raises:
        HTTPException: 404 if backup entry not found.
    """
    studio_id = await _get_studio_id(current_user, db)
    service = BackupInstructorService(db)
    backup = await service.update(studio_id, instructor_id, data)

    if not backup:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Backup instructor not found"},
        )

    return BackupInstructorResponse.model_validate(backup)


@router.delete("/{instructor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup_instructor(
    instructor_id: UUID,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove an instructor from the studio's backup network.

    Args:
        instructor_id: The instructor's profile UUID.

    Raises:
        HTTPException: 404 if backup entry not found.
    """
    studio_id = await _get_studio_id(current_user, db)
    service = BackupInstructorService(db)
    deleted = await service.delete(studio_id, instructor_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Backup instructor not found"},
        )
