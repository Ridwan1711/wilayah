from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db_session
from app.services.postal_code_service import PostalCodeService
from app.utils.response import success_response

router = APIRouter(prefix="/api/v1/postal-codes", tags=["Postal Codes"])


def get_postal_code_service(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PostalCodeService:
    return PostalCodeService(session=session, cache=request.app.state.cache)


@router.get("", summary="Get postal code by village code")
async def get_postal_codes(
    village_code: Annotated[str, Query(min_length=13, max_length=13, examples=["32.05.12.2001"])],
    service: Annotated[PostalCodeService, Depends(get_postal_code_service)],
):
    data = await service.get_by_village_code(village_code=village_code)
    message = "Data retrieved successfully" if data else "Postal code data not found"
    return success_response(message=message, data=data)


@router.get("/search", summary="Search postal codes by region name, code, or postal code")
async def search_postal_codes(
    q: Annotated[str, Query(min_length=2, examples=["garut"])],
    service: Annotated[PostalCodeService, Depends(get_postal_code_service)],
):
    data = await service.search(query=q)
    message = "Data retrieved successfully" if data else "Postal code data not found"
    return success_response(message=message, data=data)
