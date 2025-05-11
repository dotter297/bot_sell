from aiogram import Router, F
from aiogram.types import Message
from app.database.db import AsyncSessionLocal
from app.database.models import Order, Subscriber, Product
from app.keyboards.main import get_main_menu
from aiogram.filters import Command
from app.config import load_config
from app.database.functions import get_all_feedbacks
from aiogram.fsm.context import FSMContext


router = Router()
config = load_config()

def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids

@router.message(Command("orders"))
async def get_orders(message: Message):
    if not is_admin(message.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            Order.__table__.select().order_by(Order.id.desc()).limit(5)
        )
        orders = result.fetchall()

    if not orders:
        await message.answer("❗ Заказов пока нет.")
        return

    for row in orders:
        order = row._mapping
        text = (
            f"🧾 <b>Заказ #{order['id']}</b>\n"
            f"👤 {order['name']}\n"
            f"📞 {order['phone']}\n"
            f"📦 {order['salt_type']} × {order['quantity']}\n"
            f"💰 {order['total']} грн\n"
            f"🚚 {order['address']}\n"
            f"💳 {order['payment']}\n"
            f"🕒 {order['created_at']}"
        )
        await message.answer(text)

@router.message(Command("clients"))
async def get_clients(message: Message):
    if not is_admin(message.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(Subscriber.__table__.count())
        total = result.scalar()
        await message.answer(f"📊 Всего подписчиков: {total}")

@router.message(Command("broadcast"))
async def start_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await message.answer("💬 Введите текст рассылки:")
    await state.set_state("broadcast_text")

@router.message(F.state == "broadcast_text")
async def process_broadcast_text(message: Message, state: FSMContext):
    text = message.text
    await state.clear()

    async with AsyncSessionLocal() as session:
        result = await session.execute(Subscriber.__table__.select())
        subs = result.fetchall()

    success = 0
    for sub in subs:
        try:
            await message.bot.send_message(sub._mapping['user_id'], text)
            success += 1
        except:
            continue

    await message.answer(f"✅ Рассылка завершена. Отправлено: {success}")

@router.message(Command("add_product"))
async def add_product(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🛒 Введите в формате:\nНазвание | Цена | URL_фото")

@router.message(F.text.contains("|") & F.text.func(lambda x: len(x.split("|")) == 3))
async def save_product(message: Message):
    if not is_admin(message.from_user.id):
        return

    name, price, photo = map(str.strip, message.text.split("|"))
    async with AsyncSessionLocal() as session:
        session.add(Product(name=name, price=int(price), photo=photo))
        await session.commit()
    await message.answer("✅ Товар добавлен.")

@router.message(Command("dell_product"))
async def delete_product(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🗑 Введите название товара для удаления.")

@router.message()
async def delete_by_name(message: Message):
    if not is_admin(message.from_user.id):
        return
    async with AsyncSessionLocal() as session:
        result = await session.execute(Product.__table__.delete().where(Product.name == message.text.strip()))
        await session.commit()
    await message.answer("✅ Удалено, если товар существовал.")

@router.message(F.text == "/feedbacks")
async def show_feedbacks(message: Message):
    if message.from_user.id not in config.admin_ids:
        return
    feedbacks = await get_all_feedbacks()
    if not feedbacks:
        await message.answer("Отзывов пока нет.")
        return

    for fb in feedbacks:
        text = f"📝 Отзыв от {fb.name}:\n{fb.feedback}"
        await message.answer(text)

