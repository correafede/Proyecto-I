import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Read from env or use default (for local development)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://federico:proceso_seguro_2026@localhost:5432/biblioteca_seguridad"
)

# For psycopg3, we need to handle the URL carefully
# Remove +psycopg and let SQLAlchemy use the default driver
if '+psycopg' in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('+psycopg://', '://')
    # Ensure it's postgresql:// format
    if not DATABASE_URL.startswith('postgresql://'):
        DATABASE_URL = 'postgresql://' + DATABASE_URL.split('://', 1)[1]

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass
