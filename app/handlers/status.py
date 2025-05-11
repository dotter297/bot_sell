from aiogram import Router, F
from aiogram.types import Message
from app.database.db import AsyncSessionLocal
from app.database.models import Order

router = Router()

@router.message(F.text.startswith("/status"))
async def check_status(message: Message):
    try:
        phone = message.text.split(maxsplit=1)[1].strip()
    except IndexError:
        await message.answer("Введите номер телефона после команды:\n/status 0501234567")
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            Order.__table__.select().where(Order.phone == phone).order_by(Order.id.desc()).limit(1)
        )
        order = result.first()

    if not order:
        await message.answer("❌ Заказ не найден.")
    else:
        await message.answer(f"✅ Ваш заказ найден! 🚚 Статус: отправлен.\n📦 ТТН: 204502XXXXXX")
