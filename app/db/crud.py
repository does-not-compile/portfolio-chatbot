from datetime import datetime, timedelta
from datetime import timezone
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update
from app.db import models
from app.core.config import settings


# --- Users ---
def get_user(db: Session, user_id: str):
    return db.get(models.User, user_id)


# --- Sessions ---
def get_session(db: Session, session_id: str):
    return db.get(models.ChatSession, session_id)


def close_expired_or_excess_sessions(db: Session, user_id: str):
    # Mark expired
    now = datetime.utcnow()
    db.execute(
        update(models.ChatSession)
        .where(
            models.ChatSession.user_id == user_id, models.ChatSession.expires_at < now
        )
        .values(status="expired")
    )
    db.commit()

    # Enforce max active
    active = (
        db.execute(
            select(models.ChatSession)
            .where(
                models.ChatSession.user_id == user_id,
                models.ChatSession.status == "active",
            )
            .order_by(models.ChatSession.created_at.desc())
        )
        .scalars()
        .all()
    )

    if len(active) > settings.MAX_ACTIVE_SESSIONS_PER_USER:
        for s in active[settings.MAX_ACTIVE_SESSIONS_PER_USER :]:
            s.status = "closed"
        db.commit()


def create_session(db: Session, user_id: str) -> models.ChatSession:
    close_expired_or_excess_sessions(db, user_id)
    new_session = models.ChatSession(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        expires_at=datetime.now(timezone.utc)
        + timedelta(seconds=settings.SESSION_TTL_SECONDS),
        status="active",
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session


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
