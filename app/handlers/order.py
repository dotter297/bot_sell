from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from app.states.order_states import OrderFSM
from app.keyboards.main import get_main_menu
from app.database.functions import save_order_to_db
from app.config import load_config
import re
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from app.database.db import AsyncSessionLocal
from app.database.models import Product
from aiogram.types import CallbackQuery, ReplyKeyboardRemove
import asyncio

router = Router()
config = load_config()

@router.message(F.text == "📦 Каталог")
async def show_catalog(message: Message):
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Product))
            products = result.scalars().all()

        if not products:
            await message.answer("❗ Каталог пуст.")
            return

        for product in products:
            text = (
                f"<b>{product.name}</b>\n"
                f"💰 Цена: {product.price} грн"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 В корзину", callback_data=f"add_to_cart:{product.id}")]
            ])
            await message.bot.send_photo(
                chat_id=message.chat.id,
                photo=product.photo,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    except OperationalError as e:
        await message.answer("❌ Ошибка базы данных. Попробуйте позже.")
        print(f"DB Error in show_catalog: {e}")

@router.callback_query(F.data.startswith("add_to_cart:"))
async def add_to_cart(callback: CallbackQuery, state: FSMContext):
    try:
        product_id = int(callback.data.split(":")[1])
        async with AsyncSessionLocal() as session:
            product = await session.get(Product, product_id)
            if not product:
                await callback.answer("❌ Товар не найден.", show_alert=True)
                return

        cart = (await state.get_data()).get("cart", [])
        cart.append({
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "photo": product.photo
        })
        await state.update_data(cart=cart)
        await callback.answer("✅ Товар добавлен в корзину.")
    except OperationalError as e:
        await callback.answer("❌ Ошибка базы данных.", show_alert=True)
        print(f"DB Error in add_to_cart: {e}")

@router.message(F.text == "💰 Корзина")
async def show_cart(message: Message, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", [])

    if not cart:
        await message.answer("🛒 Ваша корзина пуста.")
        return

    total = sum(item["price"] for item in cart)
    text = "\n".join([f"• {item['name']} – {item['price']} грн" for item in cart])
    text += f"\n\n<b>Итого: {total} грн</b>"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
        [InlineKeyboardButton(text="🗑 Очистить", callback_data="clear_cart")]
    ])

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery, state: FSMContext):
    await state.update_data(cart=[])
    await callback.message.edit_text("🧹 Корзина очищена.")
    await callback.answer()

@router.callback_query(F.data == "checkout")
async def checkout_start(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", [])
    if not cart:
        await callback.message.edit_text("🛒 Корзина пуста. Добавьте товары.")
        await callback.answer()
        return
    await callback.message.answer("Введите имя для оформления заказа:")
    await state.set_state(OrderFSM.name)
    await callback.answer()

@router.message(OrderFSM.name)
async def get_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name or len(name) < 2:
        await message.answer("❗ Введите корректное имя (минимум 2 символа).")
        return
    await state.update_data(name=name, user_id=message.from_user.id)
    await message.answer("Ваш номер телефона:")
    await state.set_state(OrderFSM.phone)

@router.message(OrderFSM.phone)
async def get_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not re.fullmatch(r"\+?\d{10,13}", phone):
        await message.answer("❗ Введите корректный номер телефона (например: +380501234567)")
        return
    await state.update_data(phone=phone)
    await message.answer("Укажите город и отделение Новой Пошты / адрес доставки:")
    await state.set_state(OrderFSM.address)

@router.message(OrderFSM.address)
async def get_address(message: Message, state: FSMContext):
    address = message.text.strip()
    if not address or len(address) < 5:
        await message.answer("❗ Введите корректный адрес (минимум 5 символов).")
        return
    await state.update_data(address=address)
    await message.answer(
        "Выберите способ оплаты:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💳 Предоплата на карту")],
                [KeyboardButton(text="📦 Наложенный платёж")]
            ],
            resize_keyboard=True
        )
    )
    await state.set_state(OrderFSM.payment)

@router.message(OrderFSM.payment)
async def get_payment(message: Message, state: FSMContext):
    if message.text not in ["💳 Предоплата на карту", "📦 Наложенный платёж"]:
        await message.answer("❗ Выберите способ оплаты.")
        return
    await state.update_data(payment=message.text)

    data = await state.get_data()
    cart = data.get("cart", [])
    total = sum(item["price"] for item in cart)

    summary = "\n".join([f"• {item['name']} – {item['price']} грн" for item in cart])
    summary += (
        f"\n\n👤 Имя: {data['name']}"
        f"\n📞 Телефон: {data['phone']}"
        f"\n📍 Адрес: {data['address']}"
        f"\n💳 Оплата: {data['payment']}"
        f"\n💰 Итого: <b>{total} грн</b>"
        "\n\nПодтвердите заказ? (да / нет)"
    )

    await state.update_data(total=total)
    await message.answer(summary, parse_mode="HTML")
    await state.set_state(OrderFSM.confirm)

@router.message(OrderFSM.confirm)
async def confirm_order(message: Message, state: FSMContext):
    if message.text.lower() not in ["да", "нет"]:
        await message.answer("Введите 'да' или 'нет'.")
        return

    if message.text.lower() == "нет":
        await state.clear()
        await message.answer("❌ Заказ отменён.", reply_markup=get_main_menu())
        return

    data = await state.get_data()
    try:
        await save_order_to_db(data)

        cart = data.get("cart", [])
        cart_text = "\n".join([f"• {item['name']} – {item['price']} грн" for item in cart])
        total = data["total"]
        admin_text = (
            f"📦 Новый заказ!\n\n"
            f"{cart_text}\n\n"
            f"👤 Имя: {data['name']}\n"
            f"📞 Телефон: {data['phone']}\n"
            f"📍 Адрес: {data['address']}\n"
            f"💳 Оплата: {data['payment']}\n"
            f"💰 Сумма: {total} грн"
        )

        for admin_id in config.admin_ids:
            try:
                await message.bot.send_message(admin_id, admin_text, parse_mode="HTML")
                print(f"Уведомление отправлено админу {admin_id}")
            except Exception as e:
                print(f"Ошибка отправки админу {admin_id}: {e}")

        # Уведомление пользователю
        user_text = (
            "✅ Ваш заказ принят и ожидает подтверждения администратором.\n"
            "Мы свяжемся с вами после обработки заказа."
        )
        if data["payment"] == "💳 Предоплата на карту":
            user_text += f"\n\n💳 Для предоплаты переведите {total} грн на карту: <b>{config.card_number}</b>"
        elif data["payment"] == "📦 Наложенный платёж":
            user_text += "\n\n📦 Оплата при получении. Подготовьте сумму на месте."

        await message.answer(user_text, reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
        await asyncio.sleep(0.5)  # Увеличенная задержка
        await message.answer("Главное меню:", reply_markup=get_main_menu())
    except OperationalError as e:
        await message.answer("❌ Ошибка сохранения заказа. Попробуйте позже.")
        print(f"DB Error in confirm_order: {e}")
    except Exception as e:
        await message.answer("❌ Неизвестная ошибка. Попробуйте позже.")
        print(f"Unexpected error in confirm_order: {e}")
    finally:
        await state.clear()  # Гарантированная очистка состоянияая очистка состояния