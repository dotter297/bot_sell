from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
import os
import ast
from app.database.db import AsyncSessionLocal
from app.database.models import UserQuestion

load_dotenv()

class AskAdmin(StatesGroup):
    typing_question = State()

admin_ids_raw = os.getenv("ADMIN_IDS", "[]")
ADMIN_IDS = ast.literal_eval(admin_ids_raw)

router = Router()

@router.message(F.text == "💬 Задать вопрос")
async def ask_admin_command(message: Message, state: FSMContext):
    await message.answer("✏️ Введіть ваше запитання для адміністратора:")
    await state.set_state(AskAdmin.typing_question)


@router.message(AskAdmin.typing_question)
async def forward_question_to_admin(message: Message, state: FSMContext):
    # Сохраняем вопрос в базу
    async with AsyncSessionLocal() as session:
        session.add(UserQuestion(
            user_id=message.from_user.id,
            username=message.from_user.username,
            question=message.text
        ))
        await session.commit()

    for admin_id in ADMIN_IDS:
        await message.bot.send_message(
            chat_id=admin_id,
            text=f"📩 Питання від @{message.from_user.username} (ID {message.from_user.id}):\n\n{message.text}"
        )

    await message.answer("✅ Ваше запитання надіслано адміністратору.")
    await state.clear()