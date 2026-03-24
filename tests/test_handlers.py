"""Tests for bot handlers."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from src.bot.handlers.command import handle_start, handle_my
from src.bot.handlers.callback import handle_my_subscription
from src.bot.handlers.referral import handle_referral, process_referral_start
from src.bot.handlers.admin import handle_stats, is_admin
from src.models.user import User


class TestCommandHandlers:
    """Tests for command handlers."""

    @pytest.mark.asyncio
    async def test_handle_start_new_user(
        self,
        mock_message,
        mock_env,
    ):
        """Test /start command for new user."""
        with patch("src.bot.handlers.command.get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(
                scalar_one_or_none=MagicMock(return_value=None)
            ))
            mock_session.add = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()

            mock_get_session.return_value.__aiter__.return_value = [mock_session]

            await handle_start(mock_message)

            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_start_existing_user(
        self,
        mock_message,
        user,
        mock_env,
    ):
        """Test /start command for existing user."""
        with patch("src.bot.handlers.command.get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(
                scalar_one_or_none=MagicMock(return_value=user)
            ))
            mock_get_session.return_value.__aiter__.return_value = [mock_session]

            await handle_start(mock_message)

            mock_session.add.assert_not_called()
            mock_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_my_with_subscription(
        self,
        mock_message,
        user,
        subscription,
        mock_env,
    ):
        """Test /my command with active subscription."""
        with patch("src.bot.handlers.command.get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(
                scalar_one_or_none=MagicMock(return_value=user)
            ))
            mock_get_session.return_value.__aiter__.return_value = [mock_session]

            with patch("src.bot.handlers.command.SubscriptionService") as MockService:
                mock_service = AsyncMock()
                mock_service.get_user_subscription = AsyncMock(
                    return_value=subscription
                )
                MockService.return_value = mock_service

                await handle_my(mock_message)

                mock_message.answer.assert_called_once()
                call_args = mock_message.answer.call_args[0][0]
                assert "Ваша подписка" in call_args

    @pytest.mark.asyncio
    async def test_handle_my_no_subscription(
        self,
        mock_message,
        user,
        mock_env,
    ):
        """Test /my command without subscription."""
        with patch("src.bot.handlers.command.get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(
                scalar_one_or_none=MagicMock(return_value=user)
            ))
            mock_get_session.return_value.__aiter__.return_value = [mock_session]

            with patch("src.bot.handlers.command.SubscriptionService") as MockService:
                mock_service = AsyncMock()
                mock_service.get_user_subscription = AsyncMock(return_value=None)
                MockService.return_value = mock_service

                await handle_my(mock_message)

                mock_message.answer.assert_called_once()
                call_args = mock_message.answer.call_args[0][0]
                assert "нет активной подписки" in call_args


class TestCallbackHandlers:
    """Tests for callback handlers."""

    @pytest.mark.asyncio
    async def test_handle_my_subscription(
        self,
        mock_callback_query,
        user,
        subscription,
        mock_env,
    ):
        """Test my subscription callback."""
        with patch("src.bot.handlers.callback.get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(
                scalar_one_or_none=MagicMock(return_value=user)
            ))
            mock_get_session.return_value.__aiter__.return_value = [mock_session]

            with patch("src.bot.handlers.callback.SubscriptionService") as MockService:
                mock_service = AsyncMock()
                mock_service.get_user_subscription = AsyncMock(
                    return_value=subscription
                )
                MockService.return_value = mock_service

                await handle_my_subscription(mock_callback_query)

                mock_callback_query.message.edit_text.assert_called_once()


class TestReferralHandlers:
    """Tests for referral handlers."""

    @pytest.mark.asyncio
    async def test_handle_referral(
        self,
        mock_callback_query,
        user,
        mock_env,
    ):
        """Test referral info command."""
        with patch("src.bot.handlers.referral.get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(
                scalar_one_or_none=MagicMock(return_value=user)
            ))
            mock_session.commit = AsyncMock()
            mock_get_session.return_value.__aiter__.return_value = [mock_session]

            await handle_referral(mock_callback_query)

            mock_callback_query.message.edit_text.assert_called_once()
            call_args = mock_callback_query.message.edit_text.call_args[0][0]
            assert "Реферальная программа" in call_args

    @pytest.mark.asyncio
    async def test_process_referral_start(
        self,
        mock_message,
        user,
        mock_env,
    ):
        """Test referral processing on start."""
        # Create referrer
        referrer = MagicMock()
        referrer.telegram_id = 999999999

        # Create referred user (without referral)
        referred = User(
            telegram_id=mock_message.from_user.id,
            username="newuser",
            referral_code=None,
            referred_by=None,
        )

        with patch("src.bot.handlers.referral.get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(
                scalar_one_or_none=MagicMock(return_value=referred)
            ))
            mock_get_session.return_value.__aiter__.return_value = [mock_session]

            with patch("src.bot.handlers.referral.ReferralService") as MockService:
                mock_service = AsyncMock()
                mock_service.get_referrer_by_code = AsyncMock(return_value=referrer)
                mock_service.track_referral = AsyncMock(return_value=MagicMock())
                MockService.return_value = mock_service

                result = await process_referral_start(mock_message, "ABC123DEF456")

                assert result is True
                mock_service.track_referral.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_referral_self_referral(
        self,
        mock_message,
        user,
        mock_env,
    ):
        """Test self-referral prevention."""
        referred = User(
            telegram_id=mock_message.from_user.id,
            username="newuser",
            referral_code="USERCODE123",
            referred_by=None,
        )

        with patch("src.bot.handlers.referral.get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock(return_value=MagicMock(
                scalar_one_or_none=MagicMock(return_value=referred)
            ))
            mock_get_session.return_value.__aiter__.return_value = [mock_session]

            with patch("src.bot.handlers.referral.ReferralService") as MockService:
                mock_service = AsyncMock()
                # User is trying to use their own code
                mock_service.get_referrer_by_code = AsyncMock(return_value=referred)
                MockService.return_value = mock_service

                result = await process_referral_start(mock_message, "USERCODE123")

                assert result is False
                mock_service.track_referral.assert_not_called()


class TestAdminHandlers:
    """Tests for admin handlers."""

    def test_is_admin_true(self, monkeypatch):
        """Test admin check for admin user."""
        monkeypatch.setenv("ADMIN_TELEGRAM_ID", "123456789")

        # Reload settings
        import importlib
        from src.core import config
        importlib.reload(config)

        from src.bot.handlers.admin import is_admin

        result = asyncio.run(is_admin(123456789))
        assert result is True

    def test_is_admin_false(self, monkeypatch):
        """Test admin check for regular user."""
        monkeypatch.setenv("ADMIN_TELEGRAM_ID", "123456789")

        import importlib
        from src.core import config
        importlib.reload(config)

        from src.bot.handlers.admin import is_admin

        result = asyncio.run(is_admin(999999999))
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_stats(
        self,
        mock_message,
        user,
        subscription,
        payment,
        monkeypatch,
    ):
        """Test /stats command."""
        monkeypatch.setenv("ADMIN_TELEGRAM_ID", "123456789")

        with patch("src.bot.handlers.admin.get_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_get_session.return_value.__aiter__.return_value = [mock_session]

            # Mock is_admin
            with patch("src.bot.handlers.admin.is_admin", return_value=True):
                await handle_stats(mock_message)

                mock_message.answer.assert_called_once()


# Import asyncio for tests
import asyncio
