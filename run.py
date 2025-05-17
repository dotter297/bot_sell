from aiogram import Bot, Dispatcher
from app.config import load_config
from app.handlers import main_menu, order, feedback, broadcast, admin, status
from aiogram.client.default import DefaultBotProperties
from app.database.create_db import  create_tables
from sqlalchemy.orm import relationship
from app.database.db import init_db
from app.database.functions import get_db
from app.handlers import user

config = load_config()
bot = Bot(
    token=config.bot_token,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher()

# Регистрация роутеров
for router in [main_menu.router, order.router, user.router, feedback.router, broadcast.router, admin.router, status.router]:
    dp.include_router(router)

if __name__ == '__main__':
    import asyncio


    async def on_startup():
        await init_db()  # Создаём таблицы
        print("База данных готова, бот стартовал.")

    async def main():
        await create_tables()
        async for _ in get_db():
            pass
        await dp.start_polling(bot)

    asyncio.run(main())
