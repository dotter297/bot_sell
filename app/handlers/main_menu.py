from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    # Строим главное меню
    kb = ReplyKeyboardBuilder()
    kb.button(text="📦 Каталог")
    kb.button(text="💰 Корзина")
    kb.button(text="📢 Отзывы")
    kb.button(text="📢 Отзывы оставить")
    kb.button(text="💬 Задать вопрос")
    kb.button(text="🔔 Подписаться на акции")
    kb.button(text="📦 Статус заказа")
    kb.adjust(2, 2, 1)  # по 2 кнопки в ряду, последняя в отдельной строке

    await message.answer(
        text="Добро пожаловать 👋\nВыберите, что вас интересует:",
        reply_markup=kb.as_markup(resize_keyboard=True),
    )

