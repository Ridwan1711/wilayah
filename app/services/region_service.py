from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import RedisCache
from app.models.region import Region


REGION_LENGTHS = {
    "province": 2,
    "regency": 5,
    "district": 8,
    "village": 13,
}


def get_region_level(code: str) -> str:
    segment_count = len(code.split("."))
    return {
        1: "province",
        2: "regency",
        3: "district",
        4: "village",
    }.get(segment_count, "unknown")


def get_parent_code(code: str) -> str | None:
    segments = code.split(".")
    if len(segments) <= 1:
        return None
    return ".".join(segments[:-1])


def serialize_region(region: Region) -> dict[str, str | None]:
    return {
        "code": region.code,
        "name": region.name,
        "level": get_region_level(region.code),
        "parent_code": get_parent_code(region.code),
    }


class RegionService:
    def __init__(self, session: AsyncSession, cache: RedisCache) -> None:
        self.session = session
        self.cache = cache

    async def get_provinces(self) -> list[dict[str, str | None]]:
        return await self._cached_list(
            key="regions:provinces",
            statement=select(Region).where(Region.code.not_like("%.")).order_by(Region.code),
        )

    async def get_regencies(self, province_code: str) -> list[dict[str, str | None]]:
        return await self._cached_list(
            key=f"regions:regencies:{province_code}",
            statement=select(Region)
            .where(Region.code.like(f"{province_code}.%"), Region.code.not_like(f"{province_code}.%.%"))
            .order_by(Region.code),
        )

    async def get_districts(self, regency_code: str) -> list[dict[str, str | None]]:
        return await self._cached_list(
            key=f"regions:districts:{regency_code}",
            statement=select(Region)
            .where(Region.code.like(f"{regency_code}.%"), Region.code.not_like(f"{regency_code}.%.%"))
            .order_by(Region.code),
        )

    async def get_villages(self, district_code: str) -> list[dict[str, str | None]]:
        return await self._cached_list(
            key=f"regions:villages:{district_code}",
            statement=select(Region)
            .where(Region.code.like(f"{district_code}.%"), Region.code.not_like(f"{district_code}.%.%"))
            .order_by(Region.code),
        )

    async def get_detail(self, code: str) -> dict[str, str | None] | None:
        key = f"regions:detail:{code}"
        cached = await self.cache.get(key)
        if cached is not None:
            return cached

        region = await self.session.get(Region, code)
        if region is None:
            return None

        data = serialize_region(region)
        await self.cache.set(key, data)
        return data

    async def search(self, query: str, limit: int = 50) -> list[dict[str, str | None]]:
        normalized_query = query.strip()
        key = f"regions:search:{normalized_query.lower()}:{limit}"
        cached = await self.cache.get(key)
        if cached is not None:
            return cached

        statement = (
            select(Region)
            .where(or_(Region.name.ilike(f"%{normalized_query}%"), Region.code.ilike(f"{normalized_query}%")))
            .order_by(Region.code)
            .limit(limit)
        )
        result = await self.session.scalars(statement)
        data = [serialize_region(region) for region in result.all()]
        await self.cache.set(key, data)
        return data

    async def _cached_list(self, key: str, statement: Select[tuple[Region]]) -> list[dict[str, str | None]]:
        cached = await self.cache.get(key)
        if cached is not None:
            return cached

        result = await self.session.scalars(statement)
        data = [serialize_region(region) for region in result.all()]
        await self.cache.set(key, data)
        return data
