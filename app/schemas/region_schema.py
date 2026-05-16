from pydantic import BaseModel, Field


class RegionSchema(BaseModel):
    code: str = Field(examples=["32.05.12.2001"])
    name: str = Field(examples=["Garut Kota"])
    level: str = Field(examples=["village"])
    parent_code: str | None = Field(default=None, examples=["32.05.12"])
