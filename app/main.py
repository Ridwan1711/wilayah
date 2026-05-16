from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.cache import RedisCache
from app.core.config import get_settings
from app.core.cors import configure_cors
from app.routers import health, postal_codes, regions
from app.utils.response import error_response

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.cache = RedisCache(settings)
    yield
    await app.state.cache.close()


app = FastAPI(
    title=settings.app_name,
    description=(
        "Open Source API untuk data Wilayah Indonesia. "
        "Dibuat untuk dropdown alamat bertingkat: Provinsi, Kabupaten/Kota, "
        "Kecamatan, Desa/Kelurahan, dan deteksi kode pos jika data tersedia."
    ),
    version="0.1.0",
    debug=settings.app_debug,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

configure_cors(app, settings)

app.include_router(health.router)
app.include_router(regions.router)
app.include_router(postal_codes.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors: dict[str, list[str]] = {}
    for error in exc.errors():
        location = [str(item) for item in error.get("loc", []) if item not in {"query", "path", "body"}]
        field = ".".join(location) or "request"
        errors.setdefault(field, []).append(str(error.get("msg", "Invalid value")))
    return error_response(message="Validation error", errors=errors, status_code=422)


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(_: Request, __: SQLAlchemyError) -> JSONResponse:
    return error_response(
        message="Database error",
        errors={"database": ["Unable to process request"]},
        status_code=500,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, __: Exception) -> JSONResponse:
    return error_response(
        message="Internal server error",
        errors={"server": ["Unexpected error"]},
        status_code=500,
    )


@app.get("/", include_in_schema=False)
async def root() -> dict[str, Any]:
    return {
        "success": True,
        "message": "API is running",
        "data": {
            "app": settings.app_name,
            "docs": "/docs",
            "redoc": "/redoc",
        },
    }
