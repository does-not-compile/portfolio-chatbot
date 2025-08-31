from core.config import settings
from core.logger import logger
from datetime import datetime, timedelta, timezone
from db.session import get_db
from db import crud
from fastapi import Request
import jwt
from sqlalchemy.orm import Session
from typing import Optional


def create_jwt(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(days=7)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def verify_jwt(token: str) -> Optional[str]:
    payload = None
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload["sub"]
    except jwt.InvalidSignatureError:
        logger.error(f"signature of token is invalid.")
    except jwt.ExpiredSignatureError:
        logger.error(f"token for {payload['sub']} is expired.")
    except jwt.InvalidTokenError:
        logger.error(f"token for {payload['sub']} is invalid.")
    return None


def get_current_user(request: Request, db: Session) -> Optional[str]:
    token = request.cookies.get("access_token")
    user_id = None
    if token:
        user_id = verify_jwt(token)
    if user_id:
        if crud.get_user(db, user_id):
            return user_id
    return None
