from fastapi import APIRouter

from . import routes

api_router = APIRouter(prefix="/profiles")
api_router.include_router(routes.router)
