from fastapi import APIRouter

from auth.user import User2Self, create_user, CreateUser, User
from db import SessionDep

router = APIRouter()


@router.post("/register", response_model=User2Self)
def register_user(user_data: CreateUser, session: SessionDep) -> User:
    return create_user(user_data, session)
