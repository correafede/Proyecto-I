import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Read from env or use default (for local development)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://federico:proceso_seguro_2026@localhost:5432/biblioteca_seguridad"
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass
