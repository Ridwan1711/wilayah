#!/usr/bin/env sh
set -eu

echo "Loading wilayah seed data..."
sed -E 's/\) ENGINE=MyISAM;/);/g' /seed/wilayah.sql \
  | psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB"

echo "Loading postal code seed data..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" < /seed/wilayah_kodepos.sql

echo "Creating query indexes..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'SQL'
CREATE INDEX IF NOT EXISTS wilayah_code_prefix_idx ON wilayah (kode text_pattern_ops);
CREATE INDEX IF NOT EXISTS wilayah_level_idx ON wilayah ((array_length(string_to_array(kode, '.'), 1)));
CREATE INDEX IF NOT EXISTS wilayah_parent_idx ON wilayah ((regexp_replace(kode, '\.[^.]+$', '')));
CREATE INDEX IF NOT EXISTS wilayah_lower_name_idx ON wilayah (lower(nama));
CREATE INDEX IF NOT EXISTS wilayah_kodepos_value_idx ON wilayah_kodepos (kodepos);
SQL
