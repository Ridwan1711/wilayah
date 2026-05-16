"""create region tables and indexes

Revision ID: 20260516_0001
Revises:
Create Date: 2026-05-16 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260516_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS wilayah (
            kode varchar(13) PRIMARY KEY,
            nama varchar(100) NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS wilayah_kodepos (
            kode varchar(13) PRIMARY KEY REFERENCES wilayah(kode) ON DELETE CASCADE,
            kodepos varchar(5)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS wilayah_name_idx ON wilayah (nama)")
    op.execute("CREATE INDEX IF NOT EXISTS wilayah_code_prefix_idx ON wilayah (kode text_pattern_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS wilayah_level_idx ON wilayah ((array_length(string_to_array(kode, '.'), 1)))")
    op.execute("CREATE INDEX IF NOT EXISTS wilayah_parent_idx ON wilayah ((regexp_replace(kode, '\\.[^.]+$', '')))")
    op.execute("CREATE INDEX IF NOT EXISTS wilayah_lower_name_idx ON wilayah (lower(nama))")
    op.execute("CREATE INDEX IF NOT EXISTS wilayah_kodepos_value_idx ON wilayah_kodepos (kodepos)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS wilayah_kodepos_value_idx")
    op.execute("DROP INDEX IF EXISTS wilayah_lower_name_idx")
    op.execute("DROP INDEX IF EXISTS wilayah_parent_idx")
    op.execute("DROP INDEX IF EXISTS wilayah_level_idx")
    op.execute("DROP INDEX IF EXISTS wilayah_code_prefix_idx")
    op.execute("DROP INDEX IF EXISTS wilayah_name_idx")
    op.execute("DROP TABLE IF EXISTS wilayah_kodepos")
    op.execute("DROP TABLE IF EXISTS wilayah")
