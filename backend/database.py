"""
LinkedIn Platform — Database Connections
Handles MySQL (SQLAlchemy) and MongoDB (motor) connections.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

# ─── MySQL (SQLAlchemy) ─────────────────────────────────────────
engine = create_engine(
    settings.MYSQL_URL,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── MongoDB (motor — async) ────────────────────────────────────
mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
mongo_db = mongo_client[settings.MONGO_DATABASE]

# Collections
event_logs_collection = mongo_db["event_logs"]
agent_traces_collection = mongo_db["agent_traces"]
agent_tasks_collection = mongo_db["agent_tasks"]


def get_mongo():
    """Returns the MongoDB database instance."""
    return mongo_db
