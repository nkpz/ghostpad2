from typing import Any, Dict, List, Optional
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship
from .base import Base
from .message_attachment import MessageAttachment


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    extra_data = Column(JSON)  # For message-specific data like model used, tokens, etc.
    parent_message_id = Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"))

    # Self-referential relationship for threading/replies
    parent_message = relationship(
        "Message", remote_side=[id], back_populates="child_messages"
    )
    child_messages = relationship(
        "Message", back_populates="parent_message", cascade="all, delete-orphan"
    )

    # Relationship to attachments
    attachments = relationship(
        "MessageAttachment", back_populates="message", cascade="all, delete-orphan"
    )

    def attach_to_entity(
        self, entity_type: str, entity_id: int, sequence_order: Optional[int] = None
    ) -> "MessageAttachment":
        """Attach this message to any entity"""
        attachment = MessageAttachment(
            message=self,
            entity_type=entity_type,
            entity_id=entity_id,
            sequence_order=sequence_order,
        )
        self.attachments.append(attachment)
        return attachment

    def get_attached_entities(self) -> List[Dict[str, Any]]:
        """Get all entities this message is attached to"""
        return [
            {
                "entity_type": att.entity_type,
                "entity_id": att.entity_id,
                "sequence_order": att.sequence_order,
            }
            for att in self.attachments
        ]

    def __repr__(self):
        content_preview = (
            self.content[:50] + "..." if len(self.content) > 50 else self.content
        )
        return (
            f"<Message(id={self.id}, role='{self.role}', content='{content_preview}')>"
        )
