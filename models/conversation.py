from typing import List
import uuid
from sqlalchemy import JSON, Column, DateTime, String, func
from sqlalchemy.orm import relationship
from .base import Base
from .message import Message
from .message_attachment import MessageAttachment


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    extra_data = Column(
        JSON
    )  # For conversation-specific settings, model preferences, etc.

    # Relationship to get message attachments for this conversation
    message_attachments = relationship(
        "MessageAttachment",
        primaryjoin="and_(Conversation.id==MessageAttachment.entity_id, "
        "MessageAttachment.entity_type=='conversation')",
        cascade="all, delete-orphan",
        foreign_keys="MessageAttachment.entity_id",
    )

    @property
    def messages(self) -> List["Message"]:
        """Get all messages for this conversation in order"""
        return [
            ma.message
            for ma in sorted(
                self.message_attachments, key=lambda x: x.sequence_order or 0
            )
        ]

    def add_message(
        self, message: "Message", sequence_order: int
    ) -> "MessageAttachment":
        """Add a message to this conversation with explicit sequence_order"""
        attachment = MessageAttachment(
            message=message,
            entity_type="conversation",
            entity_id=self.id,
            sequence_order=sequence_order,
        )
        self.message_attachments.append(attachment)
        return attachment

    def get_message_count(self) -> int:
        """Get total number of messages in this conversation"""
        return len(self.message_attachments)

    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title}', messages={self.get_message_count()})>"
