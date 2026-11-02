from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


# Validate database configuration
if not settings.DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is missing. Please configure it in your .env file."
    )


# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
)


# Create database session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Base class for database models
Base = declarative_base()


# Database dependency
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()