from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Каталог"), KeyboardButton(text="💰 Корзина")],
            [KeyboardButton(text="📢 Отзывы"), KeyboardButton(text="💬 Задать вопрос")],
            [KeyboardButton(text="🔔 Подписаться на акции"), KeyboardButton(text="📢 Отзывы оставить")],
            [KeyboardButton(text="📦 Статус заказа")]
        ],
        resize_keyboard=True
    )