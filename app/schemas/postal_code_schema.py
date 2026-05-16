from pydantic import BaseModel, Field


class PostalCodeSchema(BaseModel):
    village_code: str = Field(examples=["32.05.12.2001"])
    postal_code: str | None = Field(default=None, examples=["44111"])
    village_name: str | None = Field(default=None, examples=["Pakuwon"])
    district_code: str | None = Field(default=None, examples=["32.05.12"])
    regency_code: str | None = Field(default=None, examples=["32.05"])
    province_code: str | None = Field(default=None, examples=["32"])
