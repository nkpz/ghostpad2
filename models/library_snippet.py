from sqlalchemy import Column, DateTime, Integer, String, Text, func
from .base import Base


class LibrarySnippet(Base):
    __tablename__ = "library_snippets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(
        String(50), nullable=False
    )  # e.g., 'system_prompt', 'user_description'
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<LibrarySnippet(id={self.id}, type='{self.type}', name='{self.name}')>"
