from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import OperationalError
from app.database.db import AsyncSessionLocal
from app.database.models import Order
import re

class OrderStatus(StatesGroup):
    waiting_for_phone = State()

router = Router()

@router.message(F.text == "📦 Статус заказа")
async def ask_for_phone(message: Message, state: FSMContext):
    await message.answer("📲 Введите номер телефона, указанный при заказе (например: +380501234567):")
    await state.set_state(OrderStatus.waiting_for_phone)

@router.message(OrderStatus.waiting_for_phone)
async def check_order_status(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not re.fullmatch(r"\+?\d{10,13}", phone):
        await message.answer("❗ Введите корректный номер телефона (например: +380501234567).")
        return

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Order)
                .where(Order.phone == phone)
                .options(selectinload(Order.items))
                .order_by(Order.id.desc())
                .limit(1)
            )
            order = result.scalar_one_or_none()

            if not order:
                await message.answer("❌ Заказ не найден. Проверьте номер телефона.")
            else:
                cart_text = "Товары не указаны" if not order.items else "\n".join(
                    [f"• {item.product_name} – {item.product_price} грн × {item.quantity}" for item in order.items]
                )
                text = (
                    f"🧾 <b>Заказ #{order.id}</b>\n"
                    f"{cart_text}\n\n"
                    f"💰 Сумма: {order.total} грн\n"
                    f"📞 Телефон: {order.phone}\n"
                    f"🚚 Адрес: {order.address}\n"
                    f"🕒 Создан: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                )
                if order.rejection_reason:
                    text += f"📦 Статус: <b>Отклонён</b>\nПричина: {order.rejection_reason}"
                elif not order.confirmed:
                    text += "📦 Статус: <b>Ожидает подтверждения</b>"
                elif order.confirmed and not order.ttn:
                    text += "📦 Статус: <b>Подтверждён</b>\nОжидает отправки."
                else:
                    text += f"📦 Статус: <b>Отправлен</b>\n📬 ТТН: <b>{order.ttn}</b>"
                await message.answer(text, parse_mode="HTML")
    except OperationalError as e:
        await message.answer("❌ Ошибка базы данных. Попробуйте позже.")
        print(f"DB Error in check_order_status: {e}")

    await state.clear()