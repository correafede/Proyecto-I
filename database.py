import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Read from env or use default (for local development)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://federico:proceso_seguro_2026@localhost:5432/biblioteca_seguridad"
)

# Ensure we use psycopg2 driver
if 'postgresql://' in DATABASE_URL and '+' not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://')
elif '+psycopg://' in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('+psycopg://', '+psycopg2://')

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass
