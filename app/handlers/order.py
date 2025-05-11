from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from app.states.order_states import OrderFSM
from app.services.calculator import calculate_price
from app.keyboards.main import get_main_menu
from app.database.functions import save_order_to_db
from app.config import load_config
import re

router = Router()
config = load_config()

SALT_TYPES = {
    "Соль таблетированная 25 кг": {
        "producer": "Sybo (Египет)",
        "guarantee": "24 мес",
        "price": 230
    }
}

@router.message(F.text == "📦каталог")
async def start_order(message: Message, state: FSMContext):
    await message.answer("Как вас зовут?")
    await state.set_state(OrderFSM.name)

@router.message(OrderFSM.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Ваш номер телефона?")
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
    await state.update_data(address=message.text)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t)] for t in SALT_TYPES],
        resize_keyboard=True
    )
    await message.answer("Выберите тип соли:", reply_markup=kb)
    await state.set_state(OrderFSM.salt_type)

@router.message(OrderFSM.salt_type)
async def get_salt_type(message: Message, state: FSMContext):
    salt_type = message.text
    if salt_type not in SALT_TYPES:
        await message.answer("❗ Пожалуйста, выберите из предложенных вариантов.")
        return
    await state.update_data(salt_type=salt_type)
    await message.answer("Сколько мешков хотите заказать?")
    await state.set_state(OrderFSM.quantity)

@router.message(OrderFSM.quantity)
async def get_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("❗ Введите положительное число.")
        return
    quantity = int(message.text)
    data = await state.get_data()
    price = SALT_TYPES[data['salt_type']]['price']
    total = calculate_price(quantity, price)
    await state.update_data(quantity=quantity, total=total)

    await message.answer(
        f"Стоимость заказа: <b>{quantity} × {price} = {total} грн</b>\n\n"
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
        await message.answer("❗ Выберите способ оплаты из кнопок.")
        return
    await state.update_data(payment=message.text)

    data = await state.get_data()
    summary = (
        f"✅ <b>Подтверждение заказа</b>:\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"📦 Тип соли: {data['salt_type']}\n"
        f"📍 Адрес: {data['address']}\n"
        f"🔢 Кол-во: {data['quantity']}\n"
        f"💳 Оплата: {data['payment']}\n"
        f"💰 Сумма: {data['total']} грн\n\n"
        "Подтвердите заказ? (да / нет)"
    )
    await message.answer(summary)
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

    # TODO: Сохранить в PostgreSQL и Google Sheets
    await message.answer("✅ Заказ принят! Мы свяжемся с вами для подтверждения.", reply_markup=get_main_menu())

    # TODO: Уведомить администратора
    await state.clear()

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

    order_data = {
        "name": data["name"],
        "phone": data["phone"],
        "address": data["address"],
        "salt_type": data["salt_type"],
        "quantity": data["quantity"],
        "total": data["total"],
        "payment": data["payment"],
    }


    # Уведомление админа
    for admin_id in config.admin_ids:
        await message.bot.send_message(admin_id, f"📦 Новый заказ от {data['name']} на сумму {data['total']} грн.")

    await message.answer("✅ Заказ принят! Мы свяжемся с вами для подтверждения.", reply_markup=get_main_menu())
    await state.clear()
