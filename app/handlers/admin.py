from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import OperationalError
from app.database.db import AsyncSessionLocal
from app.database.models import Order, Subscriber, Product, UserQuestion, Feedback
from app.keyboards.main import get_main_menu
from app.config import load_config
from dotenv import load_dotenv
import os, re

load_dotenv()
router = Router()
config = load_config()

def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids

class AddProduct(StatesGroup):
    name = State()
    price = State()
    photo = State()

class DeleteProduct(StatesGroup):
    choosing = State()

class Broadcast(StatesGroup):
    waiting_for_text = State()
    confirm = State()

class OrderAction(StatesGroup):
    rejection_reason = State()
    ttn_input = State()

class AnswerUser(StatesGroup):
    answering = State()

@router.message(Command("orders"))
async def get_orders(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Вы не админ.")
        return

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Order)
                .options(selectinload(Order.items))
                .order_by(Order.id.desc())
                .limit(5)
            )
            orders = result.scalars().all()
            print(f"Found {len(orders)} orders for admin {message.from_user.id}")

            if not orders:
                await message.answer("❗ Заказов пока нет.")
                return

            for order in orders:
                cart_text = "Товары не указаны" if not order.items else "\n".join(
                    [f"• {item.product_name} – {item.product_price} грн × {item.quantity}" for item in order.items]
                )
                status = "✅ Подтверждён" if order.confirmed else "⏳ Ожидает подтверждения"
                if order.rejection_reason:
                    status = f"❌ Отклонён: {order.rejection_reason}"
                text = (
                    f"🧾 <b>Заказ #{order.id}</b>\n"
                    f"{cart_text}\n\n"
                    f"👤 {order.name}\n"
                    f"📞 {order.phone}\n"
                    f"🚚 {order.address}\n"
                    f"💳 {order.payment}\n"
                    f"💰 {order.total} грн\n"
                    f"📦 Статус: {status}\n"
                    f"🕒 {order.created_at}"
                )
                await message.answer(text, parse_mode="HTML")
    except OperationalError as e:
        await message.answer("❌ Ошибка базы данных.")
        print(f"DB Error in get_orders: {e}")

@router.message(Command("pending_orders"))
async def get_pending_orders(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Вы не админ.")
        return

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Order)
                .options(selectinload(Order.items))
                .where(Order.confirmed == False, Order.rejection_reason == None)
                .order_by(Order.id.desc())
            )
            orders = result.scalars().all()
            print(f"Found {len(orders)} pending orders for admin {message.from_user.id}")

        if not orders:
            await message.answer("❗ Нет неподтверждённых заказов.")
            return

        for order in orders:
            cart_text = "Товары не указаны" if not order.items else "\n".join(
                [f"• {item.product_name} – {item.product_price} грн × {item.quantity}" for item in order.items]
            )
            text = (
                f"🧾 <b>Заказ #{order.id}</b>\n"
                f"{cart_text}\n\n"
                f"👤 {order.name}\n"
                f"📞 {order.phone}\n"
                f"🚚 {order.address}\n"
                f"💳 {order.payment}\n"
                f"💰 {order.total} грн\n"
                f"🕒 {order.created_at}"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_order_{order.id}")],
                [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_order_{order.id}")]
            ])
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    except OperationalError as e:
        await message.answer("❌ Ошибка базы данных.")
        print(f"DB Error in get_pending_orders: {e}")

@router.callback_query(F.data.startswith("confirm_order_"))
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ У вас нет доступа", show_alert=True)
        return

    order_id = int(callback.data.split("_")[-1])
    try:
        print(f"Processing confirm for order {order_id} by admin {callback.from_user.id}")
        async with AsyncSessionLocal() as session:
            order = await session.get(Order, order_id, options=[selectinload(Order.items)])
            if not order:
                await callback.message.edit_text("❗ Заказ не найден.")
                await callback.answer()
                return

            order.confirmed = True
            await session.commit()
            print(f"Order {order_id} confirmed")

            # Уведомление пользователю внутри сессии
            cart_text = "Товары не указаны" if not order.items else "\n".join(
                [f"• {item.product_name} – {item.product_price} грн × {item.quantity}" for item in order.items]
            )
            user_text = (
                f"✅ Ваш заказ #{order.id} подтверждён!\n\n"
                f"{cart_text}\n\n"
                f"💰 Сумма: {order.total} грн\n"
                f"📞 Телефон: {order.phone}\n"
                f"🚚 Адрес: {order.address}\n"
                f"💳 Оплата: {order.payment}"
            )
            if order.payment == "💳 Предоплата на карту":
                user_text += f"\n\n💳 Пожалуйста, переведите {order.total} грн на карту: <b>{config.card_number}</b>"
            elif order.payment == "📦 Наложенный платёж":
                user_text += "\n\n📦 Оплата при получении. Подготовьте сумму на месте."
            await callback.bot.send_message(order.user_id, user_text, parse_mode="HTML")

        await callback.message.edit_text(f"✅ Заказ #{order_id} подтверждён. Введите ТТН для отправки:")
        await state.set_state(OrderAction.ttn_input)
        await state.update_data(order_id=order_id)
        await callback.answer()
    except OperationalError as e:
        await callback.message.edit_text("❌ Ошибка базы данных.")
        print(f"DB Error in confirm_order: {e}")
        await callback.answer()

@router.message(OrderAction.ttn_input)
async def set_ttn(message: Message, state: FSMContext):
    ttn = message.text.strip()
    if not re.fullmatch(r"\d{10,14}", ttn):
        await message.answer("❗ Введите корректный ТТН (10-14 цифр).")
        return

    data = await state.get_data()
    order_id = data.get("order_id")
    try:
        print(f"Setting TTN for order {order_id}")
        async with AsyncSessionLocal() as session:
            order = await session.get(Order, order_id)
            if not order:
                await message.answer("❗ Заказ не найден.")
                await state.clear()
                return

            order.ttn = ttn
            await session.commit()
            print(f"TTN {ttn} set for order {order_id}")

            # Уведомление пользователю
            user_text = (
                f"🚚 Ваш заказ #{order.id} отправлен!\n"
                f"📦 ТТН: <b>{ttn}</b>\n"
                f"Проверьте статус доставки на сайте Новой Почты."
            )
            await message.bot.send_message(order.user_id, user_text, parse_mode="HTML")
            await message.answer(f"✅ ТТН {ttn} добавлен к заказу #{order_id}.")
    except OperationalError as e:
        await message.answer("❌ Ошибка базы данных.")
        print(f"DB Error in set_ttn: {e}")

    await state.clear()

@router.callback_query(F.data.startswith("reject_order_"))
async def reject_order(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ У вас нет доступа", show_alert=True)
        return

    order_id = int(callback.data.split("_")[-1])
    try:
        print(f"Processing reject for order {order_id} by admin {callback.from_user.id}")
        async with AsyncSessionLocal() as session:
            order = await session.get(Order, order_id)
            if not order:
                await callback.message.edit_text("❗ Заказ не найден.")
                await callback.answer()
                return

        await callback.message.edit_text("❌ Укажите причину отклонения заказа:")
        await state.set_state(OrderAction.rejection_reason)
        await state.update_data(order_id=order_id)
        await callback.answer()
    except OperationalError as e:
        await callback.message.edit_text("❌ Ошибка базы данных.")
        print(f"DB Error in reject_order: {e}")
        await callback.answer()

@router.message(OrderAction.rejection_reason)
async def set_rejection_reason(message: Message, state: FSMContext):
    reason = message.text.strip()
    if not reason or len(reason) < 5:
        await message.answer("❗ Укажите корректную причину (минимум 5 символов).")
        return

    data = await state.get_data()
    order_id = data.get("order_id")
    try:
        print(f"Setting rejection reason for order {order_id}")
        async with AsyncSessionLocal() as session:
            order = await session.get(Order, order_id, options=[selectinload(Order.items)])
            if not order:
                await message.answer("❗ Заказ не найден.")
                await state.clear()
                return

            order.rejection_reason = reason
            await session.commit()
            print(f"Rejection reason set for order {order_id}")

            # Уведомление пользователю
            cart_text = "Товары не указаны" if not order.items else "\n".join(
                [f"• {item.product_name} – {item.product_price} грн × {item.quantity}" for item in order.items]
            )
            user_text = (
                f"❌ Ваш заказ #{order.id} отклонён.\n\n"
                f"Причина: {reason}\n\n"
                f"{cart_text}\n"
                f"💰 Сумма: {order.total} грн\n"
                f"📞 Телефон: {order.phone}\n"
                f"🚚 Адрес: {order.address}"
            )
            await message.bot.send_message(order.user_id, user_text, parse_mode="HTML")
            await message.answer(f"✅ Заказ #{order_id} отклонён с причиной: {reason}")
    except OperationalError as e:
        await message.answer("❌ Ошибка базы данных.")
        print(f"DB Error in set_rejection_reason: {e}")

    await state.clear()

@router.message(Command("broadcast"))
async def start_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Вы не админ.")
        return

    await message.answer("💬 Введите текст рассылки:")
    await state.set_state(Broadcast.waiting_for_text)

@router.message(Broadcast.waiting_for_text)
async def preview_broadcast(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer("❗ Текст рассылки не может быть пустым. Попробуйте ещё раз:")
        return

    await state.update_data(text=text)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_confirm"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="broadcast_cancel")
        ]
    ])
    await message.answer(f"📢 Предпросмотр рассылки:\n\n{text}", reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(Broadcast.confirm)

@router.callback_query(F.data == "broadcast_confirm", Broadcast.confirm)
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ У вас нет доступа", show_alert=True)
        return

    data = await state.get_data()
    text = data["text"]
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Subscriber).where(Subscriber.subscribed == True))
            subscribers = result.scalars().all()

        if not subscribers:
            await callback.message.edit_text("❗ Нет активных подписчиков.")
            await callback.answer()
            await state.clear()
            return

        sent_count = 0
        failed_count = 0
        for subscriber in subscribers:
            try:
                print(f"Отправка подписчику {subscriber.user_id}")
                await callback.bot.send_message(
                    chat_id=subscriber.user_id,
                    text=text,
                    parse_mode="HTML"
                )
                sent_count += 1
            except Exception as e:
                print(f"Ошибка отправки подписчику {subscriber.user_id}: {e}")
                failed_count += 1

        await callback.message.edit_text(
            f"✅ Рассылка завершена.\n"
            f"Отправлено: {sent_count} из {len(subscribers)}\n"
            f"Ошибок: {failed_count}"
        )
    except OperationalError as e:
        await callback.message.edit_text("❌ Ошибка базы данных.")
        print(f"DB Error in confirm_broadcast: {e}")
    await callback.answer()
    await state.clear()

@router.callback_query(F.data == "broadcast_cancel", Broadcast.confirm)
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Рассылка отменена.")
    await callback.answer()
    await state.clear()

@router.message(Command("add_product"))
async def start_add_product(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Вы не админ.")
        return
    await message.answer("🛒 Введите название товара:")
    await state.set_state(AddProduct.name)

@router.message(AddProduct.name)
async def product_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name or len(name) < 2:
        await message.answer("❗ Введите корректное название (минимум 2 символа).")
        return
    await state.update_data(name=name)
    await message.answer("💵 Введите цену товара (только число):")
    await state.set_state(AddProduct.price)

@router.message(AddProduct.price)
async def product_price(message: Message, state: FSMContext):
    if message.text is None or not message.text.strip().isdigit():
        await message.answer("🚫 Цена должна быть числом. Введите снова:")
        return
    await state.update_data(price=int(message.text.strip()))
    await message.answer("📸 Отправьте фото товара:")
    await state.set_state(AddProduct.photo)

@router.message(AddProduct.photo, F.photo)
async def product_photo(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        name = data["name"]
        price = data["price"]
        photo = message.photo[-1].file_id

        async with AsyncSessionLocal() as session:
            session.add(Product(name=name, price=price, photo=photo))
            await session.commit()

        await message.answer(f"✅ Товар «{name}» успешно добавлен!")
    except OperationalError as e:
        await message.answer("❌ Ошибка базы данных.")
        print(f"DB Error in product_photo: {e}")
    await state.clear()

@router.message(AddProduct.photo)
async def invalid_photo(message: Message):
    await message.answer("🚫 Пожалуйста, отправьте именно фото.")

@router.message(Command("dell_product"))
async def choose_product_to_delete(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Вы не админ.")
        return

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Product))
            products = result.scalars().all()

        if not products:
            await message.answer("❗ Товаров нет.")
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=p.name, callback_data=f"delete_{p.id}")]
                for p in products
            ]
        )
        await message.answer("🗑 Выберите товар для удаления:", reply_markup=keyboard)
        await state.set_state(DeleteProduct.choosing)
    except OperationalError as e:
        await message.answer("❌ Ошибка базы данных.")
        print(f"DB Error in choose_product_to_delete: {e}")

@router.callback_query(F.data.startswith("delete_"))
async def delete_product_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ У вас нет доступа", show_alert=True)
        return

    product_id = int(callback.data.split("_")[1])
    try:
        async with AsyncSessionLocal() as session:
            product = await session.get(Product, product_id)
            if not product:
                await callback.message.edit_text("❗ Товар не найден.")
                await callback.answer()
                return
            await session.delete(product)
            await session.commit()
        await callback.message.edit_text(f"✅ Товар «{product.name}» удалён.")
    except OperationalError as e:
        await callback.message.edit_text("❌ Ошибка базы данных.")
        print(f"DB Error in delete_product_callback: {e}")
    await callback.answer()
    await state.clear()

@router.message(Command("questions"))
async def list_questions(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Вы не админ.")
        return

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserQuestion))
            questions = result.scalars().all()

        if not questions:
            await message.answer("❗ Нет вопросов от пользователей.")
            return

        for q in questions:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✉️ Ответить", callback_data=f"answer_{q.id}")]
            ])
            await message.answer(
                f"👤 @{q.username} (ID: {q.user_id})\n"
                f"🕐 {q.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"❓ {q.question}",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    except OperationalError as e:
        await message.answer("❌ Ошибка базы данных.")
        print(f"DB Error in list_questions: {e}")

@router.callback_query(F.data.startswith("answer_"))
async def start_answering(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ У вас нет доступа", show_alert=True)
        return

    question_id = int(callback.data.split("_")[1])
    await state.set_state(AnswerUser.answering)
    await state.update_data(question_id=question_id)
    await callback.message.answer("✍️ Напишите ответ на вопрос:")
    await callback.answer()

@router.message(AnswerUser.answering)
async def send_answer_to_user(message: Message, state: FSMContext):
    data = await state.get_data()
    question_id = data.get("question_id")
    try:
        async with AsyncSessionLocal() as session:
            question = await session.get(UserQuestion, question_id)
            if not question:
                await message.answer("🚫 Вопрос не найден.")
                await state.clear()
                return

            try:
                await message.bot.send_message(
                    chat_id=question.user_id,
                    text=f"📬 Ответ администратора на ваш вопрос:\n\n❓ {question.question}\n\n💬 {message.text}",
                    parse_mode="HTML"
                )
                await message.answer("✅ Ответ успешно отправлен пользователю.")
            except Exception as e:
                await message.answer("❌ Не удалось отправить ответ пользователю.")
                print(f"Error sending answer to user {question.user_id}: {e}")
    except OperationalError as e:
        await message.answer("❌ Ошибка базы данных.")
        print(f"DB Error in send_answer_to_user: {e}")
    await state.clear()

@router.message(Command("feedbacks"))
async def list_feedbacks_for_moderation(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Вы не админ.")
        return

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Feedback).where(Feedback.confirmed == False))
            feedbacks = result.scalars().all()

        if not feedbacks:
            await message.answer("❗ Новых отзывов нет.")
            return

        for fb in feedbacks:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_fb_{fb.id}")],
                [InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_fb_{fb.id}")]
            ])
            await message.answer(
                f"👤 {fb.name} (ID: {fb.user_id})\n"
                f"🕒 {fb.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"📝 {fb.feedback}",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    except OperationalError as e:
        await message.answer("❌ Ошибка базы данных.")
        print(f"DB Error in list_feedbacks_for_moderation: {e}")

@router.callback_query(F.data.startswith("confirm_fb_"))
async def confirm_feedback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ У вас нет доступа", show_alert=True)
        return

    feedback_id = int(callback.data.split("_")[-1])
    try:
        async with AsyncSessionLocal() as session:
            feedback = await session.get(Feedback, feedback_id)
            if feedback:
                feedback.confirmed = True
                await session.commit()
                await callback.message.edit_text(
                    f"✅ Отзыв от {feedback.name} подтверждён!\n\n📝 {feedback.feedback}",
                    parse_mode="HTML"
                )
            else:
                await callback.message.edit_text("❗ Отзыв не найден.")
    except OperationalError as e:
        await callback.message.edit_text("❌ Ошибка базы данных.")
        print(f"DB Error in confirm_feedback: {e}")
    await callback.answer()

@router.callback_query(F.data.startswith("delete_fb_"))
async def delete_feedback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ У вас нет доступа", show_alert=True)
        return

    feedback_id = int(callback.data.split("_")[-1])
    try:
        async with AsyncSessionLocal() as session:
            feedback = await session.get(Feedback, feedback_id)
            if feedback:
                await session.delete(feedback)
                await session.commit()
                await callback.message.edit_text(
                    f"🗑 Отзыв от {feedback.name} удалён!\n\n📝 {feedback.feedback}",
                    parse_mode="HTML"
                )
            else:
                await callback.message.edit_text("❗ Отзыв не найден.")
    except OperationalError as e:
        await callback.message.edit_text("❌ Ошибка базы данных.")
        print(f"DB Error in delete_feedback: {e}")
    await callback.answer()