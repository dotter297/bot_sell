from sqlalchemy.ext.asyncio import create_async_engine
from app.config import load_config
from app.database.models import Base, Product, Order



async def create_tables():
    config = load_config()
    engine = create_async_engine(config.postgres_dsn, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
