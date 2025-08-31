from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db import crud
from db.session import get_db
from core.security import get_current_user
from core.context import SystemMessage, Information
from core.logger import logger
from schemas.chat import PromptRequest
from db.models import RoleEnum
from core.openai_client import openai_client
from datetime import datetime, timezone
from pathlib import Path


router = APIRouter(prefix="/chat")
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/{session_id}", response_class=HTMLResponse)
async def chat_page(request: Request, session_id: str, db: Session = Depends(get_db)):
    user_id = get_current_user(request, db)

    if not user_id:
        logger.error("Unauthorized: Token validation failed. Redirecting to login")
        request.session["flash"] = "No valid login found: Please login again."
        return RedirectResponse("/", status_code=303)

    session = crud.get_session(db, session_id)
    if not session or session.user_id != user_id or session.hidden:
        logger.error("Unauthorized: Missing or invalid session. Redirectign to login")
        return templates.TemplateResponse(
            "404.html",
            {
                "request": request,
                "msg": "This session either does not exist, or you do not have the permission to view it.",
            },
        )

    history = crud.get_history(db, session_id, limit=1000)
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "session_id": session_id,
            "now": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
            "history": history,
        },
    )


@router.post("/{session_id}/stream")
async def chat_stream(
    session_id: str,
    req: PromptRequest,
    db: Session = Depends(get_db),
    request: Request = None,
):
    user_id = get_current_user(request, db)
    if not user_id:
        logger.error("Unauthorized: No user id provided")
        return templates.TemplateResponse("login.html", {"request": request})

    session = crud.get_session(db, session_id)
    if not session or session.user_id != user_id or session.hidden:
        logger.error("Unauthorized: Missing or invalid session")
        return templates.TemplateResponse("login.html", {"request": request})

    crud.insert_message(db, session_id, user_id, req.prompt, RoleEnum.user)

    context_blocks = [
        Information.ABOUTME.value,
        Information.EDUCATION.value,
        Information.PROJECTS.value,
    ]
    history = crud.get_history(db, session_id, limit=1000)
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
