from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.connection import get_db_session
from app.utils.response import success_response

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Application health check")
async def health_check():
    settings = get_settings()
    return success_response(
        message="API is running",
        data={
            "app": settings.app_name,
            "status": "ok",
        },
    )


@router.get("/health/db", summary="Database health check")
async def database_health(session: Annotated[AsyncSession, Depends(get_db_session)]):
    await session.execute(text("SELECT 1"))
    return success_response(message="Database is connected", data={"status": "ok"})


@router.get("/health/redis", summary="Redis health check")
async def redis_health(request: Request):
    is_connected = await request.app.state.cache.ping()
    return success_response(
        message="Redis is connected" if is_connected else "Redis is unavailable",
        data={"status": "ok" if is_connected else "unavailable"},
    )
