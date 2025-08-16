# src/models.py
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum, func
from sqlalchemy.orm import declarative_base, relationship
import enum
import uuid

Base = declarative_base()


class RoleEnum(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class User(Base):
    __tablename__ = "users"
    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    activated = Column(Boolean, default=False)
    activated_at = Column(DateTime)
    last_login = Column(DateTime)
    signup_ip = Column(String(45))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    sessions = relationship("ChatSession", back_populates="user")


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    session_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    messages = relationship("ChatMessage", back_populates="session")
    user = relationship("User", back_populates="sessions")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    message_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(
        String(36), ForeignKey("chat_sessions.session_id"), nullable=False
    )
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    session = relationship("ChatSession", back_populates="messages")
