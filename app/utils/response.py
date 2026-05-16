from typing import Any

from fastapi.responses import JSONResponse


def success_response(message: str = "Data retrieved successfully", data: Any = None) -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": [] if data is None else data,
    }


def error_response(
    message: str = "Validation error",
    errors: dict[str, Any] | None = None,
    status_code: int = 400,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "errors": errors or {},
        },
    )
