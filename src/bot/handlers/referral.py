"""Referral command handlers for the bot."""

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from src.bot.keyboards import get_back_keyboard
from src.core.database import get_session
from src.models.user import User
from src.services.referral import ReferralService

logger = logging.getLogger(__name__)

referral_router = Router()


@referral_router.callback_query(F.data == "referral")
async def handle_referral(callback: CallbackQuery) -> None:
    """
    Handle referral program info.

    Args:
        callback: Callback query
    """
    async for session in get_session():
        # Get user
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return

        # Get referral service
        referral_service = ReferralService(session)

        # Get or create referral code
        referral_code = await referral_service.get_or_create_referral_code(user)

        # Get stats
        stats = await referral_service.get_referral_stats(user)

        # Create referral link
        bot_username = (await callback.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={referral_code}"

        text = (
            "🎁 <b>Реферальная программа</b>\n\n"
            "Приглашайте друзей и получайте бонусы!\n\n"
            "💰 <b>Условия:</b>\n"
            "• 10% от первого платежа друга\n"
            "• Максимум 500 ₽ с одного реферала\n"
            "• Без ограничений по количеству\n\n"
            f"📊 <b>Ваша статистика:</b>\n"
            f"• Всего рефералов: {stats['total_referrals']}\n"
            f"• Активных: {stats['active_referrals']}\n"
            f"• Заработано: {stats['total_bonus_earned']} ₽\n\n"
            f"🔗 <b>Ваша ссылка:</b>\n"
            f"<code>{referral_link}</code>\n\n"
            f"Или код: <code>{referral_code}</code>\n\n"
            "Отправьте ссылку друзьям и они получат скидку 10% на первую оплату!"
        )

        # Build keyboard with share button
        builder = InlineKeyboardBuilder()
        builder.button(text="📤 Поделиться", switch_inline_query=f"Присоединяйся к RioVPN по моей ссылке: {referral_link}")
        builder.button(text="« Назад", callback_data="main_menu")
        builder.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
        )

    await callback.answer()


@referral_router.message(Command("referral"))
async def handle_referral_command(message: Message) -> None:
    """
    Handle /referral command.

    Args:
        message: Incoming message
    """
    async for session in get_session():
        # Get user
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("❌ Пользователь не найден")
            return

        # Get referral service
        referral_service = ReferralService(session)

        # Get or create referral code
        referral_code = await referral_service.get_or_create_referral_code(user)

        # Get stats
        stats = await referral_service.get_referral_stats(user)

        # Create referral link
        bot_username = (await message.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={referral_code}"

        text = (
            f"🎁 <b>Реферальная программа</b>\n\n"
            f"📊 <b>Ваша статистика:</b>\n"
            f"• Рефералов: {stats['total_referrals']}\n"
            f"• Заработано: {stats['total_bonus_earned']} ₽\n\n"
            f"🔗 <b>Ссылка:</b>\n"
            f"<code>{referral_link}</code>"
        )

        await message.answer(text)


async def process_referral_start(
    message: Message,
    start_param: str,
) -> bool:
    """
    Process referral on user start.

    Args:
        message: Start command message
        start_param: Start parameter (referral code)

    Returns:
        True if referral was processed
    """
    if not start_param or len(start_param) > 32:
        return False

    async for session in get_session():
        # Get referred user
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        referred = result.scalar_one_or_none()

        # Don't allow self-referral or re-referral
        if not referred or referred.referred_by:
            return False

        # Get referrer
        referral_service = ReferralService(session)
        referrer = await referral_service.get_referrer_by_code(start_param)

        if not referrer or referrer.telegram_id == message.from_user.id:
            return False

        # Track referral
        await referral_service.track_referral(referrer, referred)

        # Send notification to referrer
        try:
            await message.bot.send_message(
                chat_id=referrer.telegram_id,
                text=(
                    f"🎉 <b>Новый реферал!</b>\n\n"
                    f"Пользователь {message.from_user.username or message.from_user.id} "
                    f"присоединился по вашей ссылке.\n\n"
                    f"Когда он оплатит подписку, вы получите 10% бонус!"
                ),
            )
        except Exception as e:
            logger.warning(f"Failed to notify referrer {referrer.telegram_id}: {e}")

        logger.info(f"Referral processed: {referrer.telegram_id} -> {referred.telegram_id}")

        return True

    return False
