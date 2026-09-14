"""
Database Configuration & Session Factory.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database.models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hospital_platform.db")
is_sqlite = "sqlite" in DATABASE_URL

# Automatically redirect SQLite path to writable /tmp directory if executing in Vercel serverless environment
if os.getenv("VERCEL") and is_sqlite and not DATABASE_URL.startswith("sqlite:////tmp"):
    DATABASE_URL = "sqlite:////tmp/hospital_platform.db"
    is_sqlite = True

engine_kwargs = {}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Production connection pool settings for PostgreSQL/MySQL
    engine_kwargs.update({
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    })

from sqlalchemy import event

engine = create_engine(DATABASE_URL, **engine_kwargs)

if is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=10000")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initializes database tables and migrates schema if needed."""
    Base.metadata.create_all(bind=engine)
    if is_sqlite:
        try:
            with engine.connect() as conn:
                res = conn.execute(text("PRAGMA table_info(audit_logs)"))
                existing = {row[1] for row in res.fetchall()}
                needed = {
                    "category": "VARCHAR(100) DEFAULT 'OPERATIONAL_MONITORING'",
                    "actor_id": "VARCHAR(100)",
                    "actor_role": "VARCHAR(50) DEFAULT 'SYSTEM'",
                    "resource_type": "VARCHAR(100)",
                    "resource_id": "VARCHAR(100)",
                    "status": "VARCHAR(50) DEFAULT 'SUCCESS'",
                    "privacy_level": "VARCHAR(50) DEFAULT 'STRUCTURED_NO_PHI'"
                }
                for col_name, col_type in needed.items():
                    if col_name not in existing:
                        conn.execute(text(f"ALTER TABLE audit_logs ADD COLUMN {col_name} {col_type}"))
                conn.commit()
        except Exception:
            pass


def get_db():
    """FastAPI Dependency for database session injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
