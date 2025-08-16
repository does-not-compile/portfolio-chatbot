# src/crud.py
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import List, Optional
from .models import User, ChatSession, ChatMessage, RoleEnum


class CRUD:
    @staticmethod
    def get_user(db: Session, user_id: str) -> Optional[User]:
        return db.execute(
            select(User).where(User.user_id == user_id)
        ).scalar_one_or_none()

    @staticmethod
    def create_user(db: Session, username: str, signup_ip: str) -> User:
        user = User(signup_ip=signup_ip)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_session(db: Session, session_id: str) -> Optional[ChatSession]:
        return db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        ).scalar_one_or_none()

    @staticmethod
    def create_session(db: Session, user_id: str) -> ChatSession:
        session = ChatSession(user_id=user_id)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def insert_message(
        db: Session, session_id: str, user_id: str, message: str, role: RoleEnum
    ) -> ChatMessage:
        new_msg = ChatMessage(
            session_id=session_id, user_id=user_id, role=role, message=message
        )
        db.add(new_msg)
        db.commit()
        db.refresh(new_msg)
        return new_msg

    @staticmethod
    def get_history(db: Session, session_id: str) -> List[dict]:
        results = (
            db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.asc())
            )
            .scalars()
            .all()
        )
        return [
            {
                "role": msg.role.value,
                "content": msg.message,
                "timestamp": msg.created_at.isoformat(),
            }
            for msg in results
        ]
