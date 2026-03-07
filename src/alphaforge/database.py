from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from alphaforge.models import Base


def get_engine(db_path: str = "data/alphaforge.db", echo: bool = False) -> Engine:
    """Creates a SQLAlchemy engine for the specified SQLite database path."""
    connection_url = f"sqlite:///{db_path}"
    return create_engine(
        connection_url,
        echo=echo,
        connect_args={"check_same_thread": False}  # Needed for SQLite in multi-threaded contexts like Streamlit
    )


def SessionLocal(engine: Engine) -> sessionmaker[Session]:
    """Creates a session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session(db_path: str = "data/alphaforge.db") -> Session:
    """Helper to get a new session with default configuration."""
    return SessionLocal(get_engine(db_path))()


def init_db(engine: Engine) -> None:
    """Initializes the database schema."""
    Base.metadata.create_all(bind=engine)
