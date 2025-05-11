from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from app.config import load_config
from app.handlers import main_menu, order, feedback, broadcast, admin, questions

async def main():
    config = load_config()
    bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_routers(
        main_menu.router,
        order.router,
        feedback.router,
        questions.router,
        broadcast.router,
        admin.router,
    )

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
