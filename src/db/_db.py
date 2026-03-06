from typing import Annotated

from sqlalchemy import event
from fastapi import Depends
from sqlmodel import create_engine, Session

from core import get_settings

settings = get_settings()
engine = create_engine(settings.db_url)

if settings.db_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
