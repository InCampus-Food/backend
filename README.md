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

### 4. Konfigurasi environment
```bash
cp .env.example .env  # Jika belum ada
# Edit .env sesuai konfigurasi database kamu
```

### 6. Jalankan server (Mode Development)
Gunakan script pembantu untuk menjalankan database dan API sekaligus dengan **Hot-Reload**:
```bash
./dev.sh
```

Tabel akan dibuat otomatis saat server pertama kali dijalankan.

## Migrasi (opsional, untuk production)
```bash
alembic revision --autogenerate -m "initial"
alembic upgrade head
```
