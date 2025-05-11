# app/database/functions.py

import asyncpg
from app.config import load_config
from sqlalchemy import select
from app.database.models import Feedback
from app.database.db import AsyncSessionLocal


config = load_config()

async def save_order_to_db(data: dict):
    conn = await asyncpg.connect(
        host=config.db_host,
        port=config.db_port,
        user=config.db_user,
        password=config.db_password,
        database=config.db_name
    )

    await conn.execute("""
        INSERT INTO orders (name, phone, address, salt_type, quantity, total_price, payment)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, data["name"], data["phone"], data["address"], data["salt_type"],
         data["quantity"], data["total_price"], data["payment"])

    await conn.close()

async def get_all_feedbacks():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Feedback))
        return result.scalars().all()