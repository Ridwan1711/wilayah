from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db_session
from app.services.region_service import RegionService
from app.utils.response import error_response, success_response

router = APIRouter(prefix="/api/v1", tags=["Regions"])


def get_region_service(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RegionService:
    return RegionService(session=session, cache=request.app.state.cache)


@router.get("/provinces", summary="Get all provinces")
async def get_provinces(service: Annotated[RegionService, Depends(get_region_service)]):
    return success_response(data=await service.get_provinces())


@router.get("/regencies", summary="Get regencies/cities by province code")
async def get_regencies(
    province_code: Annotated[str, Query(min_length=2, max_length=2, examples=["32"])],
    service: Annotated[RegionService, Depends(get_region_service)],
):
    return success_response(data=await service.get_regencies(province_code=province_code))


@router.get("/districts", summary="Get districts by regency/city code")
async def get_districts(
    regency_code: Annotated[str, Query(min_length=5, max_length=5, examples=["32.05"])],
    service: Annotated[RegionService, Depends(get_region_service)],
):
    return success_response(data=await service.get_districts(regency_code=regency_code))


@router.get("/villages", summary="Get villages by district code")
async def get_villages(
    district_code: Annotated[str, Query(min_length=8, max_length=8, examples=["32.05.12"])],
    service: Annotated[RegionService, Depends(get_region_service)],
):
    return success_response(data=await service.get_villages(district_code=district_code))


@router.get("/regions/{code}", summary="Get region detail by code")
async def get_region_detail(
    code: str,
    service: Annotated[RegionService, Depends(get_region_service)],
):
    region = await service.get_detail(code=code)
    if region is None:
        return error_response("Region not found", {"code": ["No region found for this code"]}, status_code=404)
    return success_response(data=region)


@router.get("/search", summary="Search regions by name or code")
async def search_regions(
    q: Annotated[str, Query(min_length=2, examples=["garut"])],
    service: Annotated[RegionService, Depends(get_region_service)],
):
    return success_response(data=await service.search(query=q))
