from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from datetime import datetime
from sqlalchemy.orm import Session
from db import crud
from db.session import get_db
from core.security import verify_jwt
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions")


def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = verify_jwt(token)
    return user_id


@router.get("/", response_class=JSONResponse)
def get_sessions(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)

    sessions = crud.get_sessions(db, user_id)
    if not sessions:
        raise HTTPException(status_code=404, detail="No sessions found")

    r = {
        "sessions": [
            {
                "id": session.session_id,
                "created_at": f"{session.created_at.isoformat()}Z",
            }
            for session in sessions
        ]
    }

    return JSONResponse(r)


@router.get("/create")
def create_session(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    new_session = crud.create_session(db, user_id)

    return RedirectResponse(f"/chat/{new_session.session_id}")
