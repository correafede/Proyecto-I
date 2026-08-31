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

# Copy startup script
COPY start.sh .
RUN chmod +x start.sh

# Run startup script
CMD ["./start.sh"]
