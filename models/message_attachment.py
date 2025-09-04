from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship
from .base import Base


class MessageAttachment(Base):
    __tablename__ = "message_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    entity_type = Column(
        String(50), nullable=False
    )  # 'conversation', 'project', 'document', etc.
    entity_id = Column(String(36), nullable=False)
    sequence_order = Column(Integer)  # For maintaining order within the entity
    created_at = Column(DateTime, default=func.now())

    # Relationships
    message = relationship("Message", back_populates="attachments")

    # Ensure a message can only be attached once to the same entity
    __table_args__ = (
        UniqueConstraint(
            "message_id", "entity_type", "entity_id", name="uq_message_entity"
        ),
    )

    def __repr__(self):
        return f"<MessageAttachment(message_id={self.message_id}, {self.entity_type}={self.entity_id})>"
