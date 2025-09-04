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


class ConversationPersona(Base):
    __tablename__ = "conversation_personas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    persona_id = Column(
        Integer, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, default=func.now())

    # Relationships
    conversation = relationship("Conversation", backref="conversation_personas")
    persona = relationship("Persona", backref="conversation_personas")

    __table_args__ = (
        UniqueConstraint(
            "conversation_id", "persona_id", name="uq_conversation_persona"
        ),
    )

    def __repr__(self):
        return f"<ConversationPersona(conversation_id={self.conversation_id}, persona_id={self.persona_id})>"
