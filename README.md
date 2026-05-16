# Wilayah Indonesia API

Open Source API untuk data Wilayah Indonesia berbasis FastAPI. Project ini disiapkan untuk kebutuhan dropdown alamat bertingkat:

Provinsi -> Kabupaten/Kota -> Kecamatan -> Desa/Kelurahan -> Kode Pos.

Data utama memakai dump yang sudah tersedia di folder `db/`:

- `db/wilayah.sql`
- `db/wilayah_kodepos.sql`

## Stack

- FastAPI
- Uvicorn
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- Pydantic
- Docker

## Struktur Project

```text
app/
  main.py
  core/
    cache.py
    config.py
    cors.py
  database/
    connection.py
  models/
    region.py
    postal_code.py
  routers/
    health.py
    postal_codes.py
    regions.py
  schemas/
    region_schema.py
    postal_code_schema.py
  services/
    region_service.py
    postal_code_service.py
  utils/
    response.py
```

## Konfigurasi ENV

Salin `.env.example` menjadi `.env`, lalu sesuaikan nilainya.

```env
APP_NAME="Wilayah Indonesia API"
APP_ENV=local
APP_DEBUG=true
APP_URL=http://localhost:8000

DATABASE_URL=postgresql+psycopg://wilayah:wilayah_password@localhost:5432/wilayah_db
REDIS_URL=redis://localhost:6379/0

ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://example.com
ALLOWED_ORIGIN_REGEX=https://.*\.example\.com

CACHE_TTL_SECONDS=86400
```

CORS hanya membaca domain dari `ALLOWED_ORIGINS` dan `ALLOWED_ORIGIN_REGEX`. Tidak ada domain yang di-hardcode di kode program.

## Menjalankan Dengan Docker

```bash
docker compose up --build
```

Service yang akan berjalan:

- API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

Saat PostgreSQL pertama kali dibuat, script init akan membaca dump di `db/`, menyesuaikan sintaks MySQL sederhana agar bisa dimuat ke PostgreSQL, lalu membuat index tambahan.

Dokumentasi otomatis:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Install Lokal Tanpa Docker

Siapkan PostgreSQL dan Redis terlebih dahulu, lalu buat virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Jalankan migration bila tabel belum ada:

```bash
alembic upgrade head
```

Import data dari dump ke PostgreSQL. File `wilayah.sql` berasal dari format MySQL, jadi hapus bagian `ENGINE=MyISAM` sebelum import.

```bash
uvicorn app.main:app --reload
```

## Format Response

Response sukses:

```json
{
  "success": true,
  "message": "Data retrieved successfully",
  "data": []
}
```

Response error:

```json
{
  "success": false,
  "message": "Validation error",
  "errors": {}
}
```

## Endpoint

### Health

```http
GET /health
GET /health/db
GET /health/redis
```

Contoh:

```json
{
  "success": true,
  "message": "API is running",
  "data": {
    "app": "Wilayah Indonesia API",
    "status": "ok"
  }
}
```

### Wilayah

```http
GET /api/v1/provinces
GET /api/v1/regencies?province_code=32
GET /api/v1/districts?regency_code=32.05
GET /api/v1/villages?district_code=32.05.12
GET /api/v1/regions/{code}
GET /api/v1/search?q=garut
```

### Kode Pos

```http
GET /api/v1/postal-codes?village_code=32.05.12.2001
GET /api/v1/postal-codes/search?q=garut
```

Jika data kode pos tidak tersedia, API tetap mengembalikan response sukses dengan pesan `Postal code data not found` dan `data: []`.

## Contoh Alur Dropdown

1. Frontend memanggil `GET /api/v1/provinces`.
2. Setelah user memilih provinsi, ambil `code` lalu panggil `GET /api/v1/regencies?province_code={code}`.
3. Setelah user memilih kabupaten/kota, panggil `GET /api/v1/districts?regency_code={code}`.
4. Setelah user memilih kecamatan, panggil `GET /api/v1/villages?district_code={code}`.
5. Setelah user memilih desa/kelurahan, panggil `GET /api/v1/postal-codes?village_code={code}`.

## Cache

Redis digunakan untuk cache endpoint read-only. Jika Redis mati atau tidak tersedia, API tetap mengambil data dari database dan tidak crash.

Contoh key:

- `regions:provinces`
- `regions:regencies:{province_code}`
- `regions:districts:{regency_code}`
- `regions:villages:{district_code}`
- `regions:detail:{code}`
- `regions:search:{q}`
- `postal_codes:village:{village_code}`
- `postal_codes:search:{q}`

## Index Database

Index yang disiapkan:

- `wilayah.kode`
- `wilayah.nama`
- prefix lookup untuk `wilayah.kode`
- level wilayah berdasarkan jumlah segment kode
- parent wilayah berdasarkan prefix kode
- `wilayah_kodepos.kodepos`

## Lisensi

Project ini menggunakan MIT License. Sumber data dump wilayah yang tersedia di folder `db/` juga mencantumkan lisensi MIT dari pembuat datanya.
