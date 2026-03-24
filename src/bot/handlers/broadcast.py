"""Admin broadcast functionality."""

import logging
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from src.bot.keyboards import get_back_keyboard
from src.bot.notifications import get_notification_service
from src.core.database import get_session
from src.core.logging import get_logger
from src.models.user import User

logger = get_logger(__name__)

broadcast_router = Router()


class BroadcastState(StatesGroup):
    """Broadcast FSM states."""

    waiting_for_message = State()
    confirming = State()


@broadcast_router.callback_query(F.data == "admin_broadcast")
async def handle_broadcast_start(callback: CallbackQuery) -> None:
    """
    Handle broadcast start command.

    Args:
        callback: Callback query
    """
    await callback.message.edit_text(
        "💬 <b>Рассылка сообщений</b>\n\n"
        "Отправьте сообщение, которое вы хотите разослать всем пользователям.\n\n"
        "Поддерживается HTML-форматирование.\n\n"
        "Для отмены отправьте /cancel",
        reply_markup=get_back_keyboard(),
    )
    await callback.answer()


@broadcast_router.message(Command("broadcast"))
async def handle_broadcast_command(message: Message, state: FSMContext) -> None:
    """
    Handle /broadcast command.

    Args:
        message: Incoming message
        state: FSM context
    """
    await message.answer(
        "💬 <b>Рассылка сообщений</b>\n\n"
        "Отправьте сообщение, которое вы хотите разослать всем пользователям.\n\n"
        "Поддерживается HTML-форматирование.\n\n"
        "Для отмены отправьте /cancel"
    )
    await state.set_state(BroadcastState.waiting_for_message)


@broadcast_router.message(StateFilter(BroadcastState.waiting_for_message))
async def handle_broadcast_message(message: Message, state: FSMContext) -> None:
    """
    Handle broadcast message input.

    Args:
        message: Incoming message
        state: FSM context
    """
    # Store message for confirmation
    await state.update_data(broadcast_message=message.html_text)
    await state.set_state(BroadcastState.confirming)

    # Show confirmation
    await message.answer(
        f"📋 <b>Подтверждение рассылки</b>\n\n"
        f"Сообщение:\n"
        f"<tg-spoiler>{message.html_text}</tg-spoiler>\n\n"
        f"Отправить это сообщение всем пользователям?",
        reply_markup=get_broadcast_confirm_keyboard(),
    )


@broadcast_router.callback_query(F.data == "broadcast_confirm")
async def handle_broadcast_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Handle broadcast confirmation.

    Args:
        callback: Callback query
        state: FSM context
    """
    data = await state.get_data()
    broadcast_message = data.get("broadcast_message")

    if not broadcast_message:
        await callback.answer("❌ Сообщение не найдено", show_alert=True)
        await state.clear()
        return

    # Send to all users
    await callback.message.edit_text("⏳ <b>Отправка рассылки...</b>")

    notification_service = get_notification_service()
    if not notification_service:
        await callback.message.edit_text(
            "❌ <b>Ошибка: сервис уведомлений не инициализирован</b>"
        )
        await state.clear()
        return

    # Get all users
    async for session in get_session():
        result = await session.execute(select(User))
        users = result.scalars().all()

        sent_count = 0
        failed_count = 0

        for user in users:
            if user.telegram_id:
                try:
                    success = await notification_service.send_message(
                        telegram_id=user.telegram_id,
                        text=broadcast_message,
                    )
                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to send broadcast to {user.telegram_id}: {e}")

        await callback.message.edit_text(
            f"✅ <b>Рассылка завершена</b>\n\n"
            f"📤 <b>Отправлено:</b> {sent_count}\n"
            f"❌ <b>Не доставлено:</b> {failed_count}\n"
            f"👥 <b>Всего пользователей:</b> {len(users)}"
        )

        logger.info(
            f"Broadcast completed: {sent_count} sent, {failed_count} failed"
        )

    await state.clear()


@broadcast_router.callback_query(F.data == "broadcast_cancel")
async def handle_broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Handle broadcast cancellation.

    Args:
        callback: Callback query
        state: FSM context
    """
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>Рассылка отменена</b>",
        reply_markup=get_back_keyboard(),
    )
    await callback.answer()


@broadcast_router.message(Command("cancel"))
async def handle_cancel(message: Message, state: FSMContext) -> None:
    """
    Handle /cancel command.

    Args:
        message: Incoming message
        state: FSM context
    """
    current_state = await state.get_state()
    if current_state in BroadcastState.__all_states__:
        await state.clear()
        await message.answer(
            "❌ <b>Отменено</b>",
            reply_markup=get_back_keyboard(),
        )


def get_broadcast_confirm_keyboard() -> Optional['InlineKeyboardMarkup']:
    """Get broadcast confirmation keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Отправить", callback_data="broadcast_confirm")
    builder.button(text="❌ Отмена", callback_data="broadcast_cancel")
    builder.adjust(2)
    return builder.as_markup()
