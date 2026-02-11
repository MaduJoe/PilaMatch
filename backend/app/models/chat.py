from sqlalchemy import Column, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID
from app.models.enums import MessageType


class ChatThread(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "chat_threads"

    scope = Column(String(20), nullable=False)
    job_post_id = Column(GUID(), ForeignKey("job_posts.id", ondelete="SET NULL"), index=True)
    contract_id = Column(GUID(), ForeignKey("contracts.id", ondelete="SET NULL"), unique=True, index=True)
    studio_id = Column(GUID(), ForeignKey("studio_profiles.id", ondelete="CASCADE"), nullable=False)
    instructor_id = Column(GUID(), ForeignKey("instructor_profiles.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    contract = relationship("Contract", back_populates="chat_thread")
    messages = relationship("ChatMessage", back_populates="thread", order_by="ChatMessage.created_at")


class ChatMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "chat_messages"

    thread_id = Column(GUID(), ForeignKey("chat_threads.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_user_id = Column(GUID(), ForeignKey("users.id"), index=True)  # Null for system messages
    message_type = Column(String(20), default=MessageType.TEXT.value, nullable=False)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)

    # Relationships
    thread = relationship("ChatThread", back_populates="messages")
