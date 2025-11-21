# database.py

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

# --------------------------
# Load environment variables
load_dotenv()  # <-- loads variables from .env automatically

# --------------------------
# Database URL (from environment variables)
DATABASE_URL = os.getenv("DATABASE_URL")

# --------------------------
# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set False in production
    poolclass=NullPool  # optional for async
)

# --------------------------
# Async session
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# --------------------------
# Base class for models
Base = declarative_base()

# --------------------------
# Dependency for FastAPI routes
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
