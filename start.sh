#!/bin/bash
# Render.com startup script for Biblioteca API

set -e

# Render provides the database URL automatically
# But we need to wait for it to be available
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable not set"
    exit 1
fi

echo "Database URL: ${DATABASE_URL%@*}@***" # Log without password

# Wait for PostgreSQL with exponential backoff
MAX_ATTEMPTS=30
ATTEMPT=1

echo "Waiting for PostgreSQL..."
while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    if python -c "
import os
from sqlalchemy import create_engine
try:
    engine = create_engine(os.getenv('DATABASE_URL'), pool_pre_ping=True, pool_size=1)
    with engine.connect() as conn:
        conn.execute('SELECT 1')
    print('PostgreSQL is ready!')
    exit(0)
except Exception as e:
    print(f'Attempt {$ATTEMPT}: Connection failed - {str(e)[:50]}')
    exit(1)
" 2>/dev/null; then
        break
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
    SLEEP_TIME=$((ATTEMPT * 2))
    echo "PostgreSQL is unavailable - sleeping ${SLEEP_TIME}s (attempt $ATTEMPT/$MAX_ATTEMPTS)"
    sleep $SLEEP_TIME
done

if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
    echo "ERROR: Could not connect to PostgreSQL after $MAX_ATTEMPTS attempts"
    exit 1
fi

echo "PostgreSQL is ready!"
echo "Initializing database..."
python init_db.py || echo "Database init had issues, continuing..."

echo "Loading data..."
python load_data.py || echo "Data loading had issues, continuing..."

echo "Starting FastAPI server on port ${PORT:-8000}..."
uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
