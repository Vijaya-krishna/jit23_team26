from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from backend.utils.config import settings

# Configure database engine based on the URL type
# For SQLite, we require connect_args={"check_same_thread": False}
# For memory-only or concurrent SQLite usage, we use StaticPool
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool if ":memory:" in settings.DATABASE_URL else None
    )
else:
    # Standard configuration for PostgreSQL and other databases
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

# Create a sessionmaker instance
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base model class
Base = declarative_base()

def get_db():
    """
    Generator function to yield database sessions.
    Ensures that database sessions are closed correctly after requests are processed.
    Follows Dependency Injection principles.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
