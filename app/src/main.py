from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.orm import Session
from openai import OpenAI
from src.db import engine, get_db, SessionLocal
from src.models import Base, RoleEnum
from src.crud import CRUD
from src.context import SystemMessage, Information
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import logging


app = FastAPI()

logger = logging.getLogger("chat_stream")
# load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if not os.getenv("ENV") == "DEV":
    print(f"ENV={os.getenv('ENV')}")
    allowed_hosts = ["chat.snagel.io", "*.chat.snagel.io"]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/login")
async def login_redirect(userId: str = Form(...), db: Session = Depends(get_db)):
    # Check if user exists
    user = CRUD.get_user(db, userId)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create a new session for this user
    session = CRUD.create_session(db, user.user_id)

    # Redirect to chat page with both userId and sessionId in query params
    return RedirectResponse(
        url=f"/chat?userId={user.user_id}&sessionId={session.session_id}",
        status_code=303,
    )


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(
    request: Request, userId: str, sessionId: str, db: Session = Depends(get_db)
):
    # Verify user exists
    user = CRUD.get_user(db, userId)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify session exists and belongs to user
    session = CRUD.get_session(db, sessionId)
    if not session or session.user_id != user.user_id:
        raise HTTPException(
            status_code=404, detail="Session not found or not linked to user"
        )

    # Get chat history
    history = CRUD.get_history(db, sessionId)

    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "userId": user.user_id,
            "sessionId": session.session_id,
            "history": history,
        },
    )


class PromptRequest(BaseModel):
    prompt: str
    sessionId: str
    userId: str


@app.post("/chat-stream")
async def chat_stream(req: PromptRequest):
    # Validate user and session using a temporary session
    try:
        with SessionLocal() as db:
            user = CRUD.get_user(db, req.userId)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            session = CRUD.get_session(db, req.sessionId)
            if not session or session.user_id != user.user_id:
                raise HTTPException(
                    status_code=403, detail="Invalid session for this user"
                )
    except Exception as e:
        logger.exception("Error during initial DB validation")
        raise HTTPException(status_code=500, detail="Internal server error")

    def event_stream():
        assistant_accum = []

        try:
            # Insert the user message into the DB
            with SessionLocal() as db:
                CRUD.insert_message(
                    db, req.sessionId, req.userId, req.prompt, RoleEnum.user
                )

            # Stream the OpenAI response
            hist = []
            with SessionLocal() as db:
                hist = CRUD.get_history(db, req.sessionId)

            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SystemMessage.SYSMSG_NORMAL.value}
                ]
                + [{"role": "assistant", "content": Information.EDUCATION.value}]
                + [{"role": "assistant", "content": Information.ABOUTME.value}]
                + [{"role": "assistant", "content": Information.PROJECTS.value}]
                + [{"role": h["role"], "content": h["content"]} for h in hist],
                stream=True,
            )

            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    assistant_accum.append(delta)
                    yield delta

            # After streaming is done, insert assistant message into DB
            if assistant_accum:
                with SessionLocal() as db:
                    CRUD.insert_message(
                        db,
                        req.sessionId,
                        req.userId,
                        "".join(assistant_accum).strip(),
                        RoleEnum.assistant,
                    )

        except Exception as e:
            logger.exception("Error during chat streaming")
            # Send a final error chunk to the client
            yield "\n[Error: Could not complete response]\n"

    return StreamingResponse(event_stream(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
