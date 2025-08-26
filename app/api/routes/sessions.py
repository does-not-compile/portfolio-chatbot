from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db import crud
from db.session import get_db
from core.security import verify_jwt
from core.openai_client import openai_client
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions")
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = verify_jwt(token)
    return user_id


@router.get("/", response_class=JSONResponse)
def get_sessions(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)

    session_ids = crud.get_session_ids(db, user_id)
    if not session_ids:
        raise HTTPException(status_code=404, detail="No sessions found")

    return JSONResponse({"session_ids": session_ids})
