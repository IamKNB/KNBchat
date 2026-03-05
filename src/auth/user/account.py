from sqlmodel import select, Session

from auth.user import User, CreateUser
from core.security import Password

__all__ = [
    "verify_password",
    "create_user",
]


def verify_password(email: str, password: str, session: Session) -> User | None:
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    if not user:
        return None
    if Password.verify_hash(password, user.password):
        return user
    return None


def create_user(user: CreateUser, session: Session) -> User:
    user.password = Password.hash(user.password)
    user2db = User.model_validate(user)
    session.add(user2db)
    session.commit()
    session.refresh(user2db)
    return user2db
