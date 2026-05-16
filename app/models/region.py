from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Region(Base):
    __tablename__ = "wilayah"

    code: Mapped[str] = mapped_column("kode", String(13), primary_key=True)
    name: Mapped[str] = mapped_column("nama", String(100), nullable=False, index=True)
