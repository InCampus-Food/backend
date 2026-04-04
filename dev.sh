#!/bin/bash

# Start infrastructure (Postgres & pgAdmin) in the background
echo "🚀 Starting infrastructure (Postgres & pgAdmin)..."
docker-compose up -d

# Wait for DB to be ready (optional but helpful)
echo "⏳ Waiting for database..."
sleep 3

# Start the FastAPI application with hot-reload
echo "🔥 Starting FastAPI application (Hot-Reload enabled)..."
./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
