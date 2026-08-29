#!/usr/bin/env python3
"""
Manual schema initialization — creates all tables directly.
Use this instead of Alembic when auth issues prevent migration.
"""

import sys
from sqlalchemy import text
from database import engine, Base
from models import *  # Import all models to register them with Base

def init_db():
    """Create all tables from models."""
    print("Creating all tables...")
    Base.metadata.create_all(engine)
    print(" ✓ Tables created successfully")
    
    # Verify tables exist
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        print(f"\nTables in database: {', '.join(tables)}")

if __name__ == "__main__":
    try:
        init_db()
        print("\n✓ Database initialized.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
