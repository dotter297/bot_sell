from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database.models import Base
from app.config import load_config

config = load_config()
engine = create_async_engine(config.postgres_dsn, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    print("Tables in metadata:", Base.metadata.tables.keys())  # Дебаг
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialization completed.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())