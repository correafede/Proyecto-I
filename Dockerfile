FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY database.py models.py load_data.py init_db.py app.py ./
COPY llm_service.py prompts.py embedding_service.py hybrid_search.py generate_embeddings.py ./
COPY biblioteca_data.csv .
COPY alembic.ini alembic/ .

# Install Python dependencies
RUN pip install --no-cache-dir sqlalchemy psycopg fastapi uvicorn requests pgvector numpy alembic

# Wait for DB, init, run migrations, generate embeddings, and run app
CMD ["sh", "-c", "\
    echo 'Waiting for Postgres...'; \
    until pg_isready -h postgres -U federico -d biblioteca_seguridad; do sleep 1; done; \
    echo 'Initializing database...'; \
    python init_db.py && \
    python load_data.py && \
    echo 'Running migrations...'; \
    alembic upgrade head && \
    echo 'Generating embeddings...'; \
    python generate_embeddings.py && \
    echo 'Starting FastAPI server...'; \
    uvicorn app:app --host 0.0.0.0 --port 8000 \
"]
