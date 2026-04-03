# inCampus Food Delivery — Backend API

FastAPI + PostgreSQL backend untuk sistem pengiriman makanan di dalam kampus.

## Swagger UI
Setelah server berjalan, akses: `http://localhost:8000/docs`

## Setup

### 1. Clone & masuk ke folder
```bash
cd incampus-backend
```

### 2. Buat virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Buat database PostgreSQL
```sql
CREATE DATABASE incampus_db;
```

### 5. Konfigurasi environment
```bash
cp .env.example .env
# Edit .env sesuai konfigurasi database kamu
```

### 6. Jalankan server
```bash
uvicorn app.main:app --reload
```

Tabel akan dibuat otomatis saat server pertama kali dijalankan.

## Migrasi (opsional, untuk production)
```bash
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

## Struktur endpoint

| Method | Endpoint | Akses | Keterangan |
|--------|----------|-------|------------|
| POST | `/auth/register` | Public | Daftar akun |
| POST | `/auth/login` | Public | Login, dapat JWT |
| GET | `/canteens` | Public | Daftar kantin buka |
| POST | `/canteens` | Canteen/Admin | Buat kantin |
| GET | `/canteens/{id}/menu` | Public | Lihat menu |
| POST | `/canteens/{id}/menu` | Canteen/Admin | Tambah menu |
| GET | `/delivery-points` | Public | Titik antar |
| POST | `/delivery-points` | Admin | Tambah titik antar |
| POST | `/orders` | Customer | Buat pesanan |
| GET | `/orders/me` | Customer | Pesanan saya |
| GET | `/orders/canteen` | Canteen | Pesanan masuk |
| PATCH | `/orders/{id}/status` | Canteen/Admin | Update status |
| POST | `/payments` | Customer | Bayar pesanan |
| GET | `/notifications` | All | Notifikasi saya |

## Role sistem

- `customer` — mahasiswa/staff, bisa pesan makanan
- `canteen` — pemilik kantin, kelola menu & status pesanan
- `admin` — akses penuh
