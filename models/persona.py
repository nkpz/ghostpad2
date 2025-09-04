from sqlalchemy import Column, DateTime, Integer, String, Text, func
from .base import Base


class Persona(Base):
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    avatar_url = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Persona(id={self.id}, name='{self.name}')>"
