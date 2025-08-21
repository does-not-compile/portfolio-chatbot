import enum
from datetime import timedelta
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.core.config import settings


class RoleEnum(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class User(Base):
    __tablename__ = "users"
    user_id = Column(CHAR(36), primary_key=True)
    created_at = Column(DateTime, default=func.now())
    affiliation = Column(String(100), nullable=True)


class ChatSession(Base):
    __tablename__ = "sessions"
    session_id = Column(CHAR(36), primary_key=True)
    user_id = Column(CHAR(36), ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(
        DateTime,
        default=lambda: func.now() + timedelta(seconds=settings.SESSION_TTL_SECONDS),
    )
    status = Column(String(16), default="active")  # active, closed, expired

    user = relationship("User")


class Message(Base):
    __tablename__ = "messages"
    id = Column(String(36), primary_key=True)
    session_id = Column(CHAR(36), ForeignKey("sessions.session_id"), index=True)
    user_id = Column(CHAR(36), ForeignKey("users.user_id"))
    role = Column(Enum(RoleEnum), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), index=True)

    session = relationship("ChatSession")
    user = relationship("User")
