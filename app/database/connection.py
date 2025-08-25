from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .. import config

# --- ENGINE CREATION CHANGE ---
# Create the SQLAlchemy engine for MySQL
# The 'connect_args' argument for SQLite has been removed.
engine = create_engine(
    config.DATABASE_URL
)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

def get_db():
    """
    FastAPI dependency to get a database session for a request.
    Ensures the session is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()