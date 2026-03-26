"""Admin user management handlers."""

import logging
from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from src.bot.keyboards import (
    get_admin_back_keyboard,
    get_admin_users_keyboard,
    get_admin_message_keyboard,
)
from src.core.config import settings
from src.core.database import get_session
from src.models.user import User
from src.models.subscription import Subscription, SubscriptionStatus

logger = logging.getLogger(__name__)

admin_manage_router = Router()


class AdminMessageState(StatesGroup):
    """FSM states for admin message sending."""

    waiting_for_user_id = State()
    waiting_for_message = State()


class AdminDeleteState(StatesGroup):
    """FSM states for admin user deletion."""

    waiting_for_delete_user_id = State()
    waiting_for_delete_confirm = State()


class AdminSubscriptionState(StatesGroup):
    """FSM states for admin subscription management."""

    waiting_for_sub_action = State()
    waiting_for_sub_user_id = State()
    waiting_for_sub_days = State()


async def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    admin_id = settings.admin_telegram_id
    if admin_id is None:
        return False
    return user_id == admin_id


@admin_manage_router.callback_query(F.data == "admin_users")
async def handle_admin_users_menu(callback: CallbackQuery) -> None:
    """Handle admin users menu."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    await callback.message.edit_text(
        "👥 <b>Управление пользователями</b>\n\n" "Выберите действие:",
        reply_markup=get_admin_users_keyboard(),
    )
    await callback.answer()


@admin_manage_router.callback_query(F.data == "admin_user_list")
async def handle_user_list(callback: CallbackQuery) -> None:
    """Handle user list view."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    async for session in get_session():
        result = await session.execute(select(User).order_by(User.created_at.desc()).limit(20))
        users = result.scalars().all()

        text = "👥 <b>Последние 20 пользователей</b>\n\n"
        for user in users:
            username = f"@{user.username}" if user.username else "N/A"
            text += f"🆔 <code>{user.telegram_id}</code> | " f"{username} | " f"{user.created_at.strftime('%d.%m.%Y')}\n"

        await callback.message.edit_text(
            text,
            reply_markup=get_admin_back_keyboard(),
        )
    await callback.answer()


@admin_manage_router.callback_query(F.data == "admin_user_search")
async def handle_user_search_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle user search start."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    await callback.message.edit_text(
        "🔍 <b>Поиск пользователя</b>\n\n" "Отправьте Telegram ID пользователя:",
        reply_markup=get_admin_back_keyboard(),
    )
    await state.set_state(AdminMessageState.waiting_for_user_id)
    await callback.answer()


@admin_manage_router.message(AdminMessageState.waiting_for_user_id)
async def handle_user_id_input(message: Message, state: FSMContext) -> None:
    """Handle user ID input for search."""
    try:
        telegram_id = int(message.text)
    except ValueError:
        await message.answer("❌ Неверный формат. Отправьте числовой ID:")
        return

    async for session in get_session():
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()

        if not user:
            await message.answer(f"❌ Пользователь {telegram_id} не найден\n\n" "Отправьте другой ID или /cancel для отмены:")
            return

        # Get user subscriptions
        sub_result = await session.execute(select(Subscription).where(Subscription.user_id == user.id))
        subscriptions = sub_result.scalars().all()

        username = f"@{user.username}" if user.username else "N/A"
        text = (
            f"👤 <b>Информация о пользователе</b>\n\n"
            f"🆔 ID: <code>{user.telegram_id}</code>\n"
            f"👤 Username: {username}\n"
            f"📅 Регистрация: {user.created_at.strftime('%d.%m.%Y')}\n\n"
            f"📱 <b>Подписки ({len(subscriptions)})</b>\n"
        )

        for sub in subscriptions:
            status_emoji = "✅" if sub.status == SubscriptionStatus.active else "❌"
            text += (
                f"{status_emoji} {sub.type.value.upper()} | "
                f"{sub.status.value} | "
                f"до {sub.expiry_date.strftime('%d.%m.%Y')}\n"
            )

        text += "\n💡 <b>Действия</b>:\n"
        text += "/sendmsg - отправить сообщение\n"
        text += "/suspend - заблокировать подписку\n"
        text += "/grant - выдать подписку\n"

        await message.answer(text, reply_markup=get_admin_back_keyboard())
        await state.clear()


@admin_manage_router.callback_query(F.data == "admin_message")
async def handle_admin_message_menu(callback: CallbackQuery) -> None:
    """Handle admin message menu."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    await callback.message.edit_text(
        "📩 <b>Отправка сообщений</b>\n\n" "Выберите тип рассылки:",
        reply_markup=get_admin_message_keyboard(),
    )
    await callback.answer()


@admin_manage_router.callback_query(F.data == "admin_msg_user")
async def handle_send_message_to_user_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle send message to user start."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    await callback.message.edit_text(
        "📩 <b>Отправить сообщение пользователю</b>\n\n" "Отправьте Telegram ID пользователя:",
        reply_markup=get_admin_back_keyboard(),
    )
    await state.set_state(AdminMessageState.waiting_for_user_id)
    await callback.answer()


@admin_manage_router.message(
    AdminMessageState.waiting_for_user_id,
    F.text,
    StateFilter(AdminMessageState.waiting_for_user_id),
)
async def handle_message_user_id_input(message: Message, state: FSMContext) -> None:
    """Handle user ID input for message sending."""
    try:
        telegram_id = int(message.text)
    except ValueError:
        await message.answer("❌ Неверный формат. Отправьте числовой ID:")
        return

    async for session in get_session():
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()

        if not user:
            await message.answer(f"❌ Пользователь {telegram_id} не найден\n\n" "Отправьте другой ID или /cancel для отмены:")
            return

        await state.update_data(target_user_id=telegram_id)
        await state.set_state(AdminMessageState.waiting_for_message)

        await message.answer(
            f"✅ Пользователь найден: @{user.username or 'N/A'}\n\n" "Отправьте сообщение, которое хотите отправить:"
        )


@admin_manage_router.message(AdminMessageState.waiting_for_message)
async def handle_message_input(message: Message, state: FSMContext) -> None:
    """Handle message input and send to user."""
    data = await state.get_data()
    target_user_id = data.get("target_user_id")

    if not target_user_id:
        await message.answer("❌ Ошибка: пользователь не указан")
        await state.clear()
        return

    message_text = message.text or message.caption or ""

    try:
        await message.bot.send_message(
            chat_id=target_user_id,
            text=f"📩 <b>Сообщение от администратора</b>\n\n{message_text}",
            parse_mode="HTML",
        )
        await message.answer(f"✅ Сообщение отправлено пользователю {target_user_id}")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки: {e}\n\n" "Возможно, бот не может писать этому пользователю.")

    await state.clear()


@admin_manage_router.callback_query(F.data == "admin_user_delete")
async def handle_delete_user_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle delete user start."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    await callback.message.edit_text(
        "🗑 <b>Удаление пользователя</b>\n\n"
        "⚠️ <b>Внимание!</b> Это действие удалит:\n"
        "• Пользователя из базы данных\n"
        "• Все подписки пользователя\n"
        "• Все платежи пользователя\n\n"
        "Отправьте Telegram ID пользователя для удаления:",
        reply_markup=get_admin_back_keyboard(),
    )
    await state.set_state(AdminDeleteState.waiting_for_delete_user_id)
    await callback.answer()


@admin_manage_router.message(AdminDeleteState.waiting_for_delete_user_id)
async def handle_delete_user_id_input(message: Message, state: FSMContext) -> None:
    """Handle user ID input for deletion."""
    try:
        telegram_id = int(message.text)
    except ValueError:
        await message.answer("❌ Неверный формат. Отправьте числовой ID:")
        return

    async for session in get_session():
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()

        if not user:
            await message.answer(f"❌ Пользователь {telegram_id} не найден\n\n" "Отправьте другой ID или /cancel для отмены:")
            return

        # Get user subscriptions
        sub_result = await session.execute(select(Subscription).where(Subscription.user_id == user.id))
        subscriptions = sub_result.scalars().all()

        username = f"@{user.username}" if user.username else "N/A"
        text = (
            f"🗑 <b>Удаление пользователя</b>\n\n"
            f"🆔 ID: <code>{user.telegram_id}</code>\n"
            f"👤 Username: {username}\n"
            f"📅 Регистрация: {user.created_at.strftime('%d.%m.%Y')}\n\n"
            f"📱 <b>Подписки ({len(subscriptions)})</b>\n"
        )

        for sub in subscriptions:
            status_emoji = "✅" if sub.status == SubscriptionStatus.active else "❌"
            text += (
                f"{status_emoji} {sub.type.value.upper()} | "
                f"{sub.status.value} | "
                f"до {sub.expiry_date.strftime('%d.%m.%Y')}\n"
            )

        text += "\n⚠️ <b>Вы уверены?</b>\n"
        text += "Отправьте <code>YES</code> для подтверждения или <code>NO</code> для отмены:"

        await state.update_data(delete_user_id=telegram_id, delete_user=user.id)
        await state.set_state(AdminDeleteState.waiting_for_delete_confirm)

        await message.answer(text, reply_markup=get_admin_back_keyboard())


@admin_manage_router.message(AdminDeleteState.waiting_for_delete_confirm)
async def handle_delete_confirm(message: Message, state: FSMContext) -> None:
    """Handle delete confirmation."""
    data = await state.get_data()
    user_id = data.get("delete_user_id")
    db_user_id = data.get("delete_user")

    if not user_id or not db_user_id:
        await message.answer("❌ Ошибка: данные пользователя не найдены")
        await state.clear()
        return

    if message.text.strip().upper() != "YES":
        await message.answer("❌ Удаление отменено")
        await state.clear()
        return

    async for session in get_session():
        try:
            # Get counts before deletion
            subs_result = await session.execute(select(Subscription).where(Subscription.user_id == db_user_id))
            subscriptions = subs_result.scalars().all()
            sub_count = len(subscriptions)

            from src.models.payment import Payment

            payments_result = await session.execute(select(Payment).where(Payment.user_id == db_user_id))
            payments = payments_result.scalars().all()
            payment_count = len(payments)

            # Delete subscriptions
            for sub in subscriptions:
                await session.delete(sub)

            # Delete payments
            for payment in payments:
                await session.delete(payment)

            # Delete user
            user = await session.get(User, db_user_id)
            if user:
                await session.delete(user)

            await session.commit()

            await message.answer(
                f"✅ Пользователь {user_id} успешно удалён\n"
                f"Удалено подписок: {sub_count}\n"
                f"Удалено платежей: {payment_count}"
            )
        except Exception as e:
            await session.rollback()
            await message.answer(f"❌ Ошибка при удалении: {e}")

    await state.clear()


@admin_manage_router.callback_query(F.data == "admin_sub_manage")
async def handle_subscription_manage_menu(callback: CallbackQuery) -> None:
    """Handle subscription management menu."""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    await callback.message.edit_text(
        "⚙️ <b>Управление подписками</b>\n\n"
        "Доступные команды:\n\n"
        "🔹 /suspend <telegram_id> - Заблокировать подписку\n"
        "🔹 /grant <telegram_id> [type] [days] - Выдать подписку\n"
        "🔹 /search <telegram_id> - Найти пользователя\n\n"
        "Пример: /grant 123456789 ru 30",
        reply_markup=get_admin_back_keyboard(),
    )
    await callback.answer()


@admin_manage_router.message(Command("cancel"))
async def handle_cancel(message: Message, state: FSMContext) -> None:
    """Handle /cancel command."""
    current_state = await state.get_state()
    if current_state in AdminMessageState.__all_states__ or current_state in AdminDeleteState.__all_states__:
        await state.clear()
        await message.answer(
            "❌ Отменено",
            reply_markup=get_admin_back_keyboard(),
        )
    else:
        await message.answer("❌ Отменено")
