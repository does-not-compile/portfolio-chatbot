from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    signup_ip: str


class UserOut(BaseModel):
    user_id: str
    activated: bool
    created_at: datetime

    class Config:
        orm_mode = True


class SessionCreate(BaseModel):
    user_id: str


class SessionOut(BaseModel):
    session_id: str
    user_id: str
    created_at: datetime

    class Config:
        orm_mode = True


class MessageCreate(BaseModel):
    session_id: str
    user_id: str
    role: str
    message: str


class MessageOut(BaseModel):
    message_id: str
    session_id: str
    user_id: str
    role: str
    message: str
    created_at: Optional[datetime]
