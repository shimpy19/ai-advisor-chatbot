import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# check_same_thread=False is required for SQLite when accessed from FastAPI's
# threadpool-backed sync endpoints; each request still gets its own Session.
connect_args = {"check_same_thread": False} if IS_SQLITE else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

if IS_SQLITE:
    # SQLite ignores FK constraints (e.g. ON DELETE CASCADE) unless this pragma is
    # set on every connection — it does not persist in the database file itself.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class Base(DeclarativeBase):
    pass


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
