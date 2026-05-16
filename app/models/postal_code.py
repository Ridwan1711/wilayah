from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PostalCode(Base):
    __tablename__ = "wilayah_kodepos"

    village_code: Mapped[str] = mapped_column(
        "kode",
        String(13),
        ForeignKey("wilayah.kode", ondelete="CASCADE"),
        primary_key=True,
    )
    postal_code: Mapped[str | None] = mapped_column("kodepos", String(5), nullable=True, index=True)
