import os
from sqlalchemy import create_engine, Engine, event
from sqlalchemy.orm import sessionmaker, Session

from alphaforge.models import Base


def get_engine(db_path: str = "data/alphaforge.db", echo: bool = False) -> Engine:
    """Creates a SQLAlchemy engine for the specified SQLite database path."""
    if db_path != ":memory:":
        db_dir = os.path.dirname(os.path.abspath(db_path))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    connection_url = f"sqlite:///{db_path}"
    engine = create_engine(
        connection_url,
        echo=echo,
        connect_args={
            "check_same_thread": False,
            "timeout": 30  # SQLite-level busy timeout in seconds
        }
    )

    # Enable WAL mode and other concurrency pragmas
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")  # 30 seconds
        cursor.close()

    return engine


def SessionLocal(engine: Engine) -> sessionmaker[Session]:
    """Creates a session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session(db_path: str = "data/alphaforge.db") -> Session:
    """Helper to get a new session with default configuration."""
    return SessionLocal(get_engine(db_path))()


def init_db(engine: Engine) -> None:
    """Initializes the database schema."""
    Base.metadata.create_all(bind=engine)
