from fastapi import APIRouter, Form, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from db.session import get_db
from db import crud
from core.security import create_jwt

router = APIRouter()


@router.post("/login")
async def login(userId: str = Form(...), db: Session = Depends(get_db)):
    user = crud.get_user(db, userId)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create JWT cookie
    token = create_jwt(user.user_id)

    # check if latest session
    session_id = crud.get_latest_session_id(db, user.user_id)
    if not session_id:
        # Create a new chat session
        session = crud.create_session(db, user.user_id)
        session_id = session.session_id

    # set user to activated
    crud.activate_user(db, user.user_id)

    # Redirect to the correct chat page
    response = RedirectResponse(url=f"/chat/{session_id}", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # set True for prod!
        max_age=60 * 60 * 24 * 7,  # 7 days
        samesite="lax",
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=False,  # set True in production
        samesite="lax",
    )

    return response
