from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db import crud
from db.session import get_db
from core.security import verify_jwt
from core.context import SystemMessage, Information
from schemas.chat import PromptRequest
from db.models import RoleEnum
from core.openai_client import openai_client
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat")
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = verify_jwt(token)
    return user_id


@router.get("/{session_id}", response_class=HTMLResponse)
def chat_page(request: Request, session_id: str, db: Session = Depends(get_db)):
    user_id = get_current_user(request)

    session = crud.get_session(db, session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Invalid session")

    history = crud.get_history(db, session_id)
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "session_id": session_id,
            "history": history,
        },
    )


@router.post("/{session_id}/stream")
def chat_stream(
    session_id: str,
    req: PromptRequest,
    db: Session = Depends(get_db),
    request: Request = None,
):
    user_id = get_current_user(request)

    session = crud.get_session(db, session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Invalid session")

    crud.insert_message(db, session_id, user_id, req.prompt, RoleEnum.user)

    context_blocks = [
        Information.ABOUTME.value,
        Information.EDUCATION.value,
        Information.PROJECTS.value,
    ]
    history = crud.get_history(db, session_id, limit=20)
    messages = [{"role": "system", "content": SystemMessage.SYSMSG_NORMAL.value}]
    for block in context_blocks:
        messages.append({"role": "assistant", "content": block})
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": req.prompt})

    def event_stream():
        assistant_accum = []
        try:
            for delta in openai_client.stream_completion(messages):
                if delta:
                    assistant_accum.append(delta)
                    yield delta
            if assistant_accum:
                crud.insert_message(
                    db,
                    session_id,
                    user_id,
                    "".join(assistant_accum).strip(),
                    RoleEnum.assistant,
                )
        except Exception as e:
            logger.exception("Error during chat streaming")
            yield "\n[Error: Could not complete response]\n"

    return StreamingResponse(event_stream(), media_type="text/plain")
