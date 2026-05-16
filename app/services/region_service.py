from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import RedisCache
from app.models.region import Region

# Cache key suffix — naikkan bila format filter berubah (invalidasi Redis lama).
_CACHE_VERSION = "v2"


def _code_segment_count():
    """Jumlah segmen kode wilayah (mis. '32.05.12' → 3)."""
    return func.cardinality(func.string_to_array(Region.code, "."))


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


def _children_statement(parent_code: str) -> Select[tuple[Region]]:
    """Anak langsung satu tingkat di bawah parent_code (bukan cucu/cicit)."""
    child_segments = len(parent_code.split(".")) + 1
    return (
        select(Region)
        .where(
            Region.code.like(f"{parent_code}.%"),
            _code_segment_count() == child_segments,
        )
        .order_by(Region.code)
    )


class RegionService:
    def __init__(self, session: AsyncSession, cache: RedisCache) -> None:
        self.session = session
        self.cache = cache

    async def get_provinces(self) -> list[dict[str, str | None]]:
        return await self._cached_list(
            key=f"regions:provinces:{_CACHE_VERSION}",
            statement=select(Region).where(_code_segment_count() == 1).order_by(Region.code),
        )

    async def get_regencies(self, province_code: str) -> list[dict[str, str | None]]:
        return await self._cached_list(
            key=f"regions:regencies:{province_code}:{_CACHE_VERSION}",
            statement=_children_statement(province_code),
        )

    async def get_districts(self, regency_code: str) -> list[dict[str, str | None]]:
        return await self._cached_list(
            key=f"regions:districts:{regency_code}:{_CACHE_VERSION}",
            statement=_children_statement(regency_code),
        )

    async def get_villages(self, district_code: str) -> list[dict[str, str | None]]:
        return await self._cached_list(
            key=f"regions:villages:{district_code}:{_CACHE_VERSION}",
            statement=_children_statement(district_code),
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
