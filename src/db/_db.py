from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine

from core import get_settings

settings = get_settings()
engine = create_engine(settings.db_url)


def get_session():
    with Session(engine) as session:
        if settings.db_url.startswith("sqlite"):
            session.connection().exec_driver_sql("PRAGMA foreign_keys=ON")
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
