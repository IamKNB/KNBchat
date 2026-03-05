from fastapi import FastAPI

from core import get_settings, lifespan
from myapp.router import router

settings = get_settings()

app = FastAPI(
    lifespan=lifespan,
              )
app.include_router(router)
