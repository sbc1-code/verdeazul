"""Database connection and initialization for VerdeAzul."""

import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_PATH = Path(__file__).parent.parent / "verdeazul.db"
SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"

_seeding = False


def _raw_engine(db_path=None):
    """Create engine without auto-seed check. Used internally."""
    path = db_path or DB_PATH
    return create_engine(f"sqlite:///{path}", echo=False)


def get_engine(db_path=None):
    global _seeding
    path = db_path or DB_PATH
    if not path.exists() and not _seeding:
        _seeding = True
        from src.seed import seed
        seed()
        _seeding = False
    return _raw_engine(path)


def get_session(engine=None):
    eng = engine or get_engine()
    Session = sessionmaker(bind=eng)
    return Session()


def init_db(engine=None):
    """Create all tables from schema.sql."""
    eng = engine or _raw_engine()
    schema_sql = SCHEMA_PATH.read_text()
    with eng.connect() as conn:
        for statement in schema_sql.split(";"):
            stmt = statement.strip()
            if stmt:
                conn.execute(text(stmt))
        conn.commit()
    return eng


def reset_db(engine=None):
    """Drop the database file and recreate."""
    if DB_PATH.exists():
        DB_PATH.unlink()
    return init_db(engine)
