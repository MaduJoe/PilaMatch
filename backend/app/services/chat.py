from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models import (
    ChatThread, ChatMessage, InstructorProfile, StudioProfile,
    ThreadScope, MessageType
)
from app.schemas.chat import ThreadCreate


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_studio_profile_id(self, user_id: UUID) -> Optional[UUID]:
        result = await self.db.execute(
            select(StudioProfile.id).where(StudioProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_instructor_profile_id(self, user_id: UUID) -> Optional[UUID]:
        result = await self.db.execute(
            select(InstructorProfile.id).where(InstructorProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_thread_by_id(self, thread_id: UUID) -> Optional[ChatThread]:
        result = await self.db.execute(
            select(ChatThread).where(ChatThread.id == thread_id)
        )
        return result.scalar_one_or_none()

    async def create_thread(self, studio_id: UUID, data: ThreadCreate) -> ChatThread:
        # Check for existing thread with same participants and scope
        conditions = [
            ChatThread.studio_id == studio_id,
            ChatThread.instructor_id == data.instructor_id,
            ChatThread.scope == data.scope,
        ]

        if data.job_post_id:
            conditions.append(ChatThread.job_post_id == data.job_post_id)
        if data.contract_id:
            conditions.append(ChatThread.contract_id == data.contract_id)

        existing = await self.db.execute(
            select(ChatThread).where(and_(*conditions))
        )
        existing_thread = existing.scalar_one_or_none()

        if existing_thread:
            return existing_thread

        thread = ChatThread(
            scope=data.scope,
            job_post_id=data.job_post_id,
            contract_id=data.contract_id,
            studio_id=studio_id,
            instructor_id=data.instructor_id,
        )
        self.db.add(thread)
        await self.db.commit()
        await self.db.refresh(thread)
        return thread

    async def get_threads_by_user(
        self, user_id: UUID, role: str
    ) -> List[ChatThread]:
        if role == "instructor":
            instructor_id = await self.get_instructor_profile_id(user_id)
            if not instructor_id:
                return []
            result = await self.db.execute(
                select(ChatThread)
                .where(ChatThread.instructor_id == instructor_id)
                .order_by(ChatThread.updated_at.desc())
            )
        else:
            studio_id = await self.get_studio_profile_id(user_id)
            if not studio_id:
                return []
            result = await self.db.execute(
                select(ChatThread)
                .where(ChatThread.studio_id == studio_id)
                .order_by(ChatThread.updated_at.desc())
            )

        return list(result.scalars().all())

    async def can_access_thread(
        self, thread_id: UUID, user_id: UUID, role: str
    ) -> bool:
        thread = await self.get_thread_by_id(thread_id)
        if not thread:
            return False

        if role == "instructor":
            instructor_id = await self.get_instructor_profile_id(user_id)
            return thread.instructor_id == instructor_id
        else:
            studio_id = await self.get_studio_profile_id(user_id)
            return thread.studio_id == studio_id

    async def create_message(
        self,
        thread_id: UUID,
        sender_user_id: UUID,
        content: str,
        message_type: MessageType = MessageType.TEXT,
    ) -> ChatMessage:
        message = ChatMessage(
            thread_id=thread_id,
            sender_user_id=sender_user_id,
            message_type=message_type,
            content=content,
        )
        self.db.add(message)

        # Update thread's updated_at
        thread = await self.get_thread_by_id(thread_id)
        if thread:
            from datetime import datetime
            thread.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def create_system_message(
        self, thread_id: UUID, content: str
    ) -> ChatMessage:
        message = ChatMessage(
            thread_id=thread_id,
            sender_user_id=None,
            message_type=MessageType.SYSTEM,
            content=content,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_messages(
        self, thread_id: UUID, limit: int = 50, before_id: Optional[UUID] = None
    ) -> List[ChatMessage]:
        query = select(ChatMessage).where(ChatMessage.thread_id == thread_id)

        if before_id:
            query = query.where(ChatMessage.id < before_id)

        query = query.order_by(ChatMessage.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        messages = list(result.scalars().all())
        return list(reversed(messages))  # Return in chronological order

    async def mark_messages_read(
        self, thread_id: UUID, user_id: UUID
    ) -> None:
        result = await self.db.execute(
            select(ChatMessage).where(
                ChatMessage.thread_id == thread_id,
                ChatMessage.sender_user_id != user_id,
                ChatMessage.is_read == False,
            )
        )
        messages = result.scalars().all()

        for message in messages:
            message.is_read = True

        await self.db.commit()

    async def get_last_message(self, thread_id: UUID) -> Optional[ChatMessage]:
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.thread_id == thread_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
