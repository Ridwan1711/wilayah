from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import RedisCache
from app.models.postal_code import PostalCode
from app.models.region import Region


def serialize_postal_code(postal_code: PostalCode, region: Region | None = None) -> dict[str, str | None]:
    village_code = postal_code.village_code
    code_parts = village_code.split(".")
    return {
        "village_code": village_code,
        "postal_code": postal_code.postal_code,
        "village_name": region.name if region else None,
        "district_code": ".".join(code_parts[:3]) if len(code_parts) >= 3 else None,
        "regency_code": ".".join(code_parts[:2]) if len(code_parts) >= 2 else None,
        "province_code": code_parts[0] if code_parts else None,
    }


class PostalCodeService:
    def __init__(self, session: AsyncSession, cache: RedisCache) -> None:
        self.session = session
        self.cache = cache

    async def get_by_village_code(self, village_code: str) -> list[dict[str, str | None]]:
        key = f"postal_codes:village:{village_code}"
        cached = await self.cache.get(key)
        if cached is not None:
            return cached

        statement = (
            select(PostalCode, Region)
            .join(Region, Region.code == PostalCode.village_code, isouter=True)
            .where(PostalCode.village_code == village_code)
        )
        rows = (await self.session.execute(statement)).all()
        data = [serialize_postal_code(postal_code, region) for postal_code, region in rows]
        await self.cache.set(key, data)
        return data

    async def search(self, query: str, limit: int = 50) -> list[dict[str, str | None]]:
        normalized_query = query.strip()
        key = f"postal_codes:search:{normalized_query.lower()}:{limit}"
        cached = await self.cache.get(key)
        if cached is not None:
            return cached

        statement = (
            select(PostalCode, Region)
            .join(Region, Region.code == PostalCode.village_code, isouter=True)
            .where(
                or_(
                    PostalCode.postal_code.ilike(f"%{normalized_query}%"),
                    PostalCode.village_code.ilike(f"{normalized_query}%"),
                    Region.name.ilike(f"%{normalized_query}%"),
                )
            )
            .order_by(PostalCode.village_code)
            .limit(limit)
        )
        rows = (await self.session.execute(statement)).all()
        data = [serialize_postal_code(postal_code, region) for postal_code, region in rows]
        await self.cache.set(key, data)
        return data
