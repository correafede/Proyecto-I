#!/bin/bash
# Render.com startup script for Biblioteca API

set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h ${DATABASE_HOST:-localhost} -U ${POSTGRES_USER:-federico} -d ${POSTGRES_DB:-biblioteca_seguridad}; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "PostgreSQL is up!"

echo "Initializing database..."
python init_db.py

echo "Loading data..."
python load_data.py

echo "Starting FastAPI server..."
uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
