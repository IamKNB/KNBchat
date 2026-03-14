from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict

# 获取项目根目录
ROOT_DIR = Path(__file__).resolve().parents[2]


# 加载环境变量
class Settings(BaseSettings):
    root_dir: Path = ROOT_DIR
    db_url: str
    port: int

    app_env: str
    log_level: str

    jwt_secret_key: str
    jwt_algorithm: str

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


# noinspection PyUnusedLocal
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    from db import init_db, dispose_db
    init_db()
    try:
        yield
    finally:
        dispose_db()


# 从缓存中获取settings
@lru_cache()
def get_settings() -> Settings:
    # noinspection PyArgumentList
    return Settings()
