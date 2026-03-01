from uuid import UUID
from typing import Dict, Set
import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, AsyncSessionLocal
from app.core.deps import get_current_user, require_role
from app.core.security import decode_access_token
from app.models import User, UserRole
from app.schemas.chat import (
    ThreadCreate,
    ThreadResponse,
    ThreadListResponse,
    MessageCreate,
    MessageResponse,
    ThreadMessagesResponse,
)
from app.services.chat import ChatService

router = APIRouter()


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}

    async def connect(self, thread_id: UUID, websocket: WebSocket):
        if thread_id not in self.active_connections:
            self.active_connections[thread_id] = set()
        self.active_connections[thread_id].add(websocket)

    def disconnect(self, thread_id: UUID, websocket: WebSocket):
        if thread_id in self.active_connections:
            self.active_connections[thread_id].discard(websocket)
            if not self.active_connections[thread_id]:
                del self.active_connections[thread_id]

    async def broadcast_to_thread(self, thread_id: UUID, message: dict):
        if thread_id in self.active_connections:
            for connection in self.active_connections[thread_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass


manager = ConnectionManager()


@router.post("", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(
    data: ThreadCreate,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat thread (studio only)."""
    service = ChatService(db)
    studio_id = await service.get_studio_profile_id(current_user.id)

    if not studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Studio profile not found"},
        )

    thread = await service.create_thread(studio_id, data)
    last_message = await service.get_last_message(thread.id)

    return ThreadResponse(
        id=thread.id,
        scope=thread.scope,
        job_post_id=thread.job_post_id,
        contract_id=thread.contract_id,
        studio_id=thread.studio_id,
        instructor_id=thread.instructor_id,
        is_active=thread.is_active,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        last_message=MessageResponse.model_validate(last_message) if last_message else None,
    )


@router.get("", response_model=ThreadListResponse)
async def get_threads(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's chat threads."""
    service = ChatService(db)
    threads = await service.get_threads_by_user(current_user.id, current_user.role)

    items = []
    for thread in threads:
        last_message = await service.get_last_message(thread.id)
        items.append(ThreadResponse(
            id=thread.id,
            scope=thread.scope,
            job_post_id=thread.job_post_id,
            contract_id=thread.contract_id,
            studio_id=thread.studio_id,
            instructor_id=thread.instructor_id,
            is_active=thread.is_active,
            created_at=thread.created_at,
            updated_at=thread.updated_at,
            last_message=MessageResponse.model_validate(last_message) if last_message else None,
        ))

    return ThreadListResponse(items=items, total=len(items))


@router.get("/{thread_id}/messages", response_model=ThreadMessagesResponse)
async def get_thread_messages(
    thread_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get messages in a thread."""
    service = ChatService(db)

    if not await service.can_access_thread(thread_id, current_user.id, current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCESS_DENIED", "message": "Not authorized to access this thread"},
        )

    thread = await service.get_thread_by_id(thread_id)
    messages = await service.get_messages(thread_id)

    # Mark messages as read
    await service.mark_messages_read(thread_id, current_user.id)

    last_message = messages[-1] if messages else None

    return ThreadMessagesResponse(
        thread=ThreadResponse(
            id=thread.id,
            scope=thread.scope,
            job_post_id=thread.job_post_id,
            contract_id=thread.contract_id,
            studio_id=thread.studio_id,
            instructor_id=thread.instructor_id,
            is_active=thread.is_active,
            created_at=thread.created_at,
            updated_at=thread.updated_at,
            last_message=MessageResponse.model_validate(last_message) if last_message else None,
        ),
        messages=[MessageResponse.model_validate(m) for m in messages],
    )


@router.post("/{thread_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    thread_id: UUID,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message in a thread."""
    service = ChatService(db)

    if not await service.can_access_thread(thread_id, current_user.id, current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCESS_DENIED", "message": "Not authorized to access this thread"},
        )

    message = await service.create_message(thread_id, current_user.id, data.content)

    # Broadcast to WebSocket connections
    await manager.broadcast_to_thread(
        thread_id,
        {
            "type": "message",
            "data": MessageResponse.model_validate(message).model_dump(mode="json"),
        },
    )

    return MessageResponse.model_validate(message)


@router.websocket("/ws/threads/{thread_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    thread_id: UUID,
):
    """WebSocket endpoint for real-time chat.

    Authentication: Send {"type": "auth", "token": "<JWT>"} as the first message.
    The connection will be closed if auth is not provided within 10 seconds.
    """
    await websocket.accept()

    # Wait for auth message (10 second timeout)
    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        auth_data = json.loads(raw)
    except (asyncio.TimeoutError, json.JSONDecodeError):
        await websocket.send_json({"type": "error", "message": "Authentication required"})
        await websocket.close(code=4001)
        return

    if auth_data.get("type") != "auth" or not auth_data.get("token"):
        await websocket.send_json({"type": "error", "message": "First message must be auth"})
        await websocket.close(code=4001)
        return

    token = auth_data["token"]
    user_id = decode_access_token(token)
    if not user_id:
        await websocket.send_json({"type": "error", "message": "Invalid token"})
        await websocket.close(code=4001)
        return

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        from app.models import User as UserModel

        result = await db.execute(select(UserModel).where(UserModel.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            await websocket.send_json({"type": "error", "message": "User not found"})
            await websocket.close(code=4001)
            return

        service = ChatService(db)
        if not await service.can_access_thread(thread_id, user.id, user.role):
            await websocket.send_json({"type": "error", "message": "Access denied"})
            await websocket.close(code=4003)
            return

    # Auth successful - send confirmation
    await websocket.send_json({"type": "auth_success", "user_id": user_id})

    await manager.connect(thread_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data.get("type") == "message":
                content = message_data.get("content", "")
                if content:
                    async with AsyncSessionLocal() as db:
                        service = ChatService(db)
                        message = await service.create_message(
                            thread_id, UUID(user_id), content
                        )

                        await manager.broadcast_to_thread(
                            thread_id,
                            {
                                "type": "message",
                                "data": MessageResponse.model_validate(message).model_dump(mode="json"),
                            },
                        )
            elif message_data.get("type") == "typing":
                await manager.broadcast_to_thread(
                    thread_id,
                    {
                        "type": "typing",
                        "data": {"user_id": user_id},
                    },
                )
    except WebSocketDisconnect:
        manager.disconnect(thread_id, websocket)
    except Exception:
        manager.disconnect(thread_id, websocket)
