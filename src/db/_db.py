from typing import Annotated

from fastapi import Depends
from sqlmodel import create_engine, Session

from core import get_settings

settings = get_settings()
engine = create_engine(settings.db_url)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
