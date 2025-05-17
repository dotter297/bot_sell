from app.database.models import Order, Feedback
from app.database.db import AsyncSessionLocal
from sqlalchemy import select
from app.database.models import Order, OrderItem

async def save_order_to_db(order_data: dict):
    order_data.pop("cart", None)

    async with AsyncSessionLocal() as session:
        order = Order(**order_data)
        session.add(order)
        await session.commit()

async def save_feedback_to_db(feedback_data: dict):
    async with AsyncSessionLocal() as session:
        feedback = Feedback(**feedback_data)
        session.add(feedback)
        await session.commit()

async def get_all_orders():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Order))
        return result.scalars().all()

async def get_all_feedbacks():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Feedback))
        return result.scalars().all()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def save_order_to_db(data: dict):
    async with AsyncSessionLocal() as session:
        print("INPUT DATA:", data)
        cart = data.get("cart", [])
        order_data = {k: v for k, v in data.items() if k != "cart"}
        print("ORDER DATA (без cart):", order_data)
        order = Order(**order_data)
        session.add(order)
        await session.flush()
        for item in cart:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item["id"],
                product_name=item["name"],
                product_price=item["price"],
                quantity=item.get("quantity", 1)
            )
            session.add(order_item)
        await session.commit()