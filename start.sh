#!/bin/bash
# Render.com startup script for Biblioteca API

set -e

# Render provides the database URL automatically
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable not set"
    exit 1
fi

# Log connection attempt (without password)
DB_LOG=$(echo $DATABASE_URL | sed 's/:[^@]*@/:PASSWORD@/')
echo "Database URL: $DB_LOG"

# Wait for PostgreSQL with exponential backoff
MAX_ATTEMPTS=30
ATTEMPT=1

echo "Waiting for PostgreSQL..."
while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    if python << 'EOF' 2>/dev/null
import os
import sys
from sqlalchemy import text, create_engine

db_url = os.getenv('DATABASE_URL')
print(f"Testing connection to database...")

try:
    # Remove +psycopg if present - let SQLAlchemy handle it
    if '+psycopg' in db_url:
        db_url_test = db_url.replace('+psycopg://', '://')
    else:
        db_url_test = db_url
    
    engine = create_engine(db_url_test, echo=False, pool_size=1, max_overflow=0)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("PostgreSQL is ready!")
        sys.exit(0)
except Exception as e:
    print(f"Connection failed: {str(e)[:100]}")
    sys.exit(1)
EOF
    then
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
