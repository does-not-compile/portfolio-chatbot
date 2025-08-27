from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from core.config import settings
from core.security import get_current_user
from core.logger import logger
from db import crud
from db.session import Base, engine, get_db
from api.routes.health import router as health_router
from api.routes.auth import router as auth_router
from api.routes.chat import router as chat_router
from api.routes.sessions import router as session_router
from pathlib import Path
from sqlalchemy.orm import Session

BASE_DIR = Path(__file__).resolve().parent

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Snagel Chat")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.ENV != "DEV":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(session_router)


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    # check if user is already logged in
    user_id = get_current_user(request)

    if user_id:
        # check if latest session
        session_id = crud.get_latest_session_id(db, user_id)
        if not session_id:
            # Create a new chat session
            session = crud.create_session(db, user_id)
            session_id = session.session_id
        return RedirectResponse(f"/chat/{session_id}", status_code=303)

    # if not, serve login template
    return templates.TemplateResponse("login.html", {"request": request})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
