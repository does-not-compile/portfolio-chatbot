from datetime import datetime, timedelta
from datetime import timezone
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update
from db import models
from core.config import settings


# --- Users ---
def get_user(db: Session, user_id: str):
    return db.get(models.User, user_id)


def activate_user(db: Session, user_id: str):
    stmt = (
        update(models.User).where(models.User.user_id == user_id).values(activated=True)
    )
    db.execute(stmt)
    db.commit()


# --- Sessions ---
def get_sessions(db: Session, user_id: str, show_hidden: bool = False):
    stmt = (
        select(models.ChatSession.session_id, models.ChatSession.created_at)
        .where(models.ChatSession.user_id == user_id)
        .where(
            models.ChatSession.hidden == show_hidden
        )  #  only return non-hidden sessions
        .order_by(models.ChatSession.created_at.desc())
    )
    result = db.execute(stmt).all()
    return result


def get_session(db: Session, session_id: str):
    return db.get(models.ChatSession, session_id)


def get_latest_session_id(db: Session, user_id: str):
    stmt = (
        select(models.Message.session_id)
        .select_from(models.Message)
        .join(
            models.ChatSession,
            models.ChatSession.session_id == models.Message.session_id,
        )
        .where(models.ChatSession.user_id == user_id)
        .where(models.ChatSession.hidden == False)
        .order_by(models.Message.created_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalar()


def create_session(db: Session, user_id: str) -> models.ChatSession:
    new_session = models.ChatSession(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session


def hide_session(db: Session, session_id: str):
    stmt = (
        update(models.ChatSession)
        .where(models.ChatSession.session_id == session_id)
        .values(hidden=True)
    )

    db.execute(stmt)
    db.commit()

    return session_id


# --- Messages ---
def insert_message(
    db: Session, session_id: str, user_id: str, content: str, role: models.RoleEnum
):
    m = models.Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        user_id=user_id,
        role=role,
        content=content,
    )
    db.add(m)
    db.commit()
    return m


def get_history(db: Session, session_id: str, limit: int = 16):
    # Return the last N messages for prompt context
    stmt = (
        select(models.Message)
        .where(models.Message.session_id == session_id)
        .order_by(models.Message.created_at.desc())
        .limit(limit)
    )
    msgs = list(reversed(db.execute(stmt).scalars().all()))
    return [
        {"role": m.role.value, "content": m.content, "created_at": m.created_at}
        for m in msgs
    ]
