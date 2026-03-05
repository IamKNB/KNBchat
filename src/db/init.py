from sqlmodel import SQLModel

from db import engine


def init_db():
    create_db_and_tables()


def dispose_db():
    engine.dispose()


def create_db_and_tables():
    # Ensure all models are imported so SQLModel metadata is populated.
    import db.models  # noqa: F401
    SQLModel.metadata.create_all(engine)
