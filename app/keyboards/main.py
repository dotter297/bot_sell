from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦каталог"), KeyboardButton(text="💰корзина")],
            [KeyboardButton(text="📢 Отзывы"), KeyboardButton(text="💬 Задать вопрос")],
            [KeyboardButton(text="🔔 Подписаться на акции")]
        ],
        resize_keyboard=True
    )
