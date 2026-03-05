from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from auth import get_user
from auth.sessions.token import Token, TokenUtils
from auth.user import User, verify_password, User2Self

__all__ = [
    "router",
]

from db import SessionDep

router = APIRouter()


@router.post("/login", response_model=Token)
def login(session: SessionDep, form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    user = verify_password(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status_code=422, detail="Incorrect username or password")
    return TokenUtils.create_token(user)


@router.get("/me", response_model=User2Self)
def user_self(user: User = Depends(get_user)) -> User:
    return user
