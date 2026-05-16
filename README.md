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
- PostgreSQL dan Redis hanya di jaringan internal Docker (hostname `postgres` / `redis`), tidak mem-publish port `5432`/`6379` ke host agar tidak bentrok di server shared (mis. Dokploy).

Untuk dev lokal yang perlu koneksi langsung ke DB/Redis dari host, salin `docker-compose.override.example.yml` menjadi `docker-compose.override.yml`.

## Deploy Dokploy (Compose Service)

1. Upload repo / set root compose ke folder `wilayah_api`.
2. Tab **Environment** — jangan pakai `localhost` untuk DB/Redis. Gunakan hostname service Docker:

```env
DATABASE_URL=postgresql+psycopg://wilayah:wilayah_password@postgres:5432/wilayah_db
REDIS_URL=redis://redis:6379/0
APP_URL=https://api-wilayah.ngedeploy.online
APP_ENV=production
APP_DEBUG=false
```

(`docker-compose.yml` juga meng-set `DATABASE_URL` / `REDIS_URL` internal; nilai di panel Dokploy jangan menimpa dengan `localhost`.)

3. Tab **Domains**: service `app`, port `8000`, path `/`, HTTPS Letsencrypt. Klik **Validate DNS** sampai hijau.
4. Domain di browser, DNS A record, `APP_URL`, dan tab Domains harus **sama persis** (mis. `api-wilayah.ngedeploy.online` — bukan `ngodingdeploy` vs `ngedeploy`).
5. Setelah ubah domain/env, wajib **Redeploy** (Compose pakai label Traefik; tidak auto-update seperti app biasa).
6. Klik **Preview Compose** — pastikan service `app` dapat label `traefik.enable=true` dan port `8000`.

### Troubleshooting `404 page not found` (teks polos, bukan JSON FastAPI)

Itu respons **Traefik**, bukan FastAPI. Artinya proxy belum menemukan backend.

| Gejala | Penyebab umum |
|--------|----------------|
| `404 page not found` | Host salah / DNS belum ke server / domain belum di-redeploy |
| `503 Service Unavailable` | Container `app` tidak jalan (postgres healthcheck gagal, crash, dll.) |
| FastAPI `{"detail":"Not Found"}` | Routing OK; path API salah |

Checklist:

- Buka domain yang **sama** dengan tab Domains (cek typo subdomain/Tld).
- Logs service `app` — harus ada baris Uvicorn `Application startup complete`.
- Jangan pakai `ports: "8000:8000"` di compose untuk Dokploy; cukup `ports: - 8000`.
- Hapus `container_name` di compose (sudah dihapus di repo ini).
- Jika `app` tidak pernah start: cek logs `postgres` (seed `./db` bisa kosong di redeploy AutoDeploy — pertimbangkan volume/file mount Dokploy).

Jika deploy gagal dengan `port is already allocated` pada `6379` atau `5432`, pastikan compose terbaru dipakai (redis/postgres tanpa `ports:` ke host).

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
