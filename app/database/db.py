from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import load_config

config = load_config()
engine = create_async_engine(config.postgres_dsn, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def save_order_to_db(order_data: dict):
    async with AsyncSessionLocal() as session:
        new_order = Order(**order_data)
        session.add(new_order)
        await session.commit()
