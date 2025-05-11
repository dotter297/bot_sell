from aiogram import Bot, Dispatcher
from app.config import load_config
from app.handlers import main_menu, order, feedback, broadcast, admin, status
from aiogram.client.default import DefaultBotProperties

config = load_config()
bot = Bot(
    token=config.bot_token,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher()

# Регистрация роутеров
for router in [main_menu.router, order.router, feedback.router, broadcast.router, admin.router, status.router]:
    dp.include_router(router)

if __name__ == '__main__':
    import asyncio
    from app.database.db import get_db


    async def main():
        # Если init_db - это асинхронный генератор
        async for _ in get_db():
            pass  # Обработка данных (если нужно)
        await dp.start_polling(bot)


    asyncio.run(main())
