from aiogram import Router, F
from aiogram.types import Message
from app.database.db import AsyncSessionLocal
from app.database.models import Feedback
from app.config import load_config

router = Router()
config = load_config()

@router.message(F.text == "📢 Отзывы")
async def show_feedbacks(message: Message):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            Feedback.__table__.select().order_by(Feedback.id.desc()).limit(3)
        )
        feedbacks = result.fetchall()

    if not feedbacks:
        await message.answer("Отзывов пока нет.")
        return

    text = "\n\n".join([f"“{f._mapping['text']}” — {f._mapping['name']}" for f in feedbacks])
    await message.answer(f"📢 Отзывы:\n\n{text}")

# Только для админов — добавление отзыва
@router.message(F.text.startswith("/add_feedback"))
async def add_feedback(message: Message):
    if message.from_user.id not in config.admin_ids:
        return

    try:
        parts = message.text.split(maxsplit=2)
        name, text = parts[1], parts[2]
    except IndexError:
        await message.answer("Используйте: /add_feedback Имя Текст_отзыва")
        return

    async with AsyncSessionLocal() as session:
        session.add(Feedback(name=name, text=text))
        await session.commit()

    await message.answer("✅ Отзыв добавлен.")

