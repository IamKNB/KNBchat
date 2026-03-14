from functools import lru_cache
from typing import Annotated, Iterator

from fastapi import Depends
from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from core import get_settings

settings = get_settings()


@lru_cache()
def get_engine() -> Engine:
    return create_engine(settings.db_url)


def get_session() -> Iterator[Session]:
    engine = get_engine()
    with Session(engine) as session:
        if settings.db_url.startswith("sqlite"):
            session.connection().exec_driver_sql("PRAGMA foreign_keys=ON")
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
