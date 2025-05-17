from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy import select
from app.database.models import Subscriber
from app.database.db import AsyncSessionLocal

router = Router()

def get_subscription_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📬 Підписатися", callback_data="subscribe"),
            InlineKeyboardButton(text="🚫 Відписатися", callback_data="unsubscribe")
        ]
    ])

@router.message(F.text == "🔔 Подписаться на акции")
async def show_subscription_options(message: Message):
    await message.answer(
        "📢 Керуйте вашою підпискою на розсилку:",
        reply_markup=get_subscription_keyboard()
    )

@router.message(Command("subscribe"))
async def subscribe_user(message: Message):
    user_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        subscriber = await session.get(Subscriber, user_id)
        if subscriber:
            if subscriber.subscribed:
                await message.answer("📬 Ви вже підписані на розсилку!")
                return
            subscriber.subscribed = True
        else:
            session.add(Subscriber(user_id=user_id))
        await session.commit()
    await message.answer("✅ Ви успішно підписалися на розсилку!")

@router.message(Command("unsubscribe"))
async def unsubscribe_user(message: Message):
    user_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        subscriber = await session.get(Subscriber, user_id)
        if subscriber and subscriber.subscribed:
            subscriber.subscribed = False
            await session.commit()
            await message.answer("🚫 Ви відписалися від розсилки.")
        else:
            await message.answer("❓ Ви не підписані на розсилку.")

@router.callback_query(F.data == "subscribe")
async def handle_subscribe(callback: CallbackQuery):
    user_id = callback.from_user.id
    print(f"Subscribe attempt for user_id: {user_id}")
    async with AsyncSessionLocal() as session:
        subscriber = await session.get(Subscriber, user_id)
        print(f"Subscriber found: {subscriber}")
        if subscriber:
            if subscriber.subscribed:
                print("User already subscribed")
                await callback.message.edit_text(
                    "📬 Ви вже підписані на розсилку!",
                    reply_markup=get_subscription_keyboard()
                )
                await callback.answer()
                return
            subscriber.subscribed = True
            print("Reactivating subscription")
        else:
            session.add(Subscriber(user_id=user_id))
            print("Adding new subscriber")
        await session.commit()
    print("Subscription successful")
    await callback.message.edit_text(
        "✅ Ви успішно підписалися на розсилку!",
        reply_markup=get_subscription_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "unsubscribe")
async def handle_unsubscribe(callback: CallbackQuery):
    user_id = callback.from_user.id
    print(f"Unsubscribe attempt for user_id: {user_id}")
    async with AsyncSessionLocal() as session:
        subscriber = await session.get(Subscriber, user_id)
        print(f"Subscriber found: {subscriber}")
        if subscriber and subscriber.subscribed:
            subscriber.subscribed = False
            await session.commit()
            print("Unsubscribed")
            await callback.message.edit_text(
                "🚫 Ви відписалися від розсилки.",
                reply_markup=get_subscription_keyboard()
            )
        else:
            print("Not subscribed")
            await callback.message.edit_text(
                "❓ Ви не підписані на розсилку.",
                reply_markup=get_subscription_keyboard()
            )
    await callback.answer()