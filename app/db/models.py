import enum
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from db.session import Base
from core.config import settings


class RoleEnum(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class User(Base):
    __tablename__ = "users"
    user_id = Column(CHAR(36), primary_key=True)
    created_at = Column(DateTime, default=func.now())
    affiliation = Column(String(100), nullable=True)
    activated = Column(Boolean, default=False)


class ChatSession(Base):
    __tablename__ = "sessions"
    session_id = Column(CHAR(36), primary_key=True)
    user_id = Column(CHAR(36), ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    hidden = Column(Boolean, default=False)  # pseudo delete of sessions

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
