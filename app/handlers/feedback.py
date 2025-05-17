from aiogram.fsm.state import StatesGroup, State
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from app.database.models import Feedback
from app.database.db import AsyncSessionLocal
from aiogram.filters import Command
from app.handlers import admin
from sqlalchemy import select

class LeaveFeedback(StatesGroup):
    writing = State()

router = Router()

@router.message(F.text == "📢 Отзывы оставить")
async def start_feedback(message: Message, state: FSMContext):
    await message.answer("✏️ Напишіть ваш відгук:")
    await state.set_state(LeaveFeedback.writing)

@router.message(LeaveFeedback.writing)
async def save_feedback(message: Message, state: FSMContext):
    async with AsyncSessionLocal() as session:
        session.add(Feedback(
            user_id=message.from_user.id,
            name=message.from_user.full_name,
            feedback=message.text
        ))
        await session.commit()
    await message.answer("✅ Дякуємо! Ваш відгук надіслано на перевірку.")
    await state.clear()

@router.message(F.text == "📢 Отзывы")
async def show_reviews(message: Message):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Feedback).where(Feedback.confirmed == True).order_by(Feedback.created_at.desc()).limit(10)
        )
        feedbacks = result.scalars().all()

    if not feedbacks:
        await message.answer("Поки немає підтверджених відгуків.")
        return

    for fb in feedbacks:
        await message.answer(f"📝 {fb.name}:\n{fb.feedback}")
