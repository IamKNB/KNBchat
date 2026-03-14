from sqlmodel import SQLModel

from db import get_engine


def init_db() -> None:
    create_db_and_tables()


def dispose_db() -> None:
    get_engine().dispose()


def create_db_and_tables() -> None:
    # Ensure all models are imported so SQLModel metadata is populated.
    import db.models  # noqa: F401
    SQLModel.metadata.create_all(get_engine())
