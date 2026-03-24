"""Internationalization (i18n) module for multi-language support."""

import gettext
import logging
from pathlib import Path
from typing import Optional

from aiogram.utils.i18n import FSMI18nMiddleware, I18nMiddleware

from src.core.logging import get_logger

logger = get_logger(__name__)

# Supported locales
SUPPORTED_LOCALES = ["ru", "en"]
DEFAULT_LOCALE = "ru"

# Locales directory
LOCALES_DIR = Path(__file__).parent.parent / "locales"


class I18n:
    """
    Internationalization manager.

    Handles locale selection and translation loading.
    """

    def __init__(self, domain: str = "messages"):
        """
        Initialize i18n.

        Args:
            domain: Translation domain name
        """
        self.domain = domain
        self.locales = {}

        # Load translations
        for locale in SUPPORTED_LOCALES:
            locale_path = LOCALES_DIR / locale / "LC_MESSAGES"
            if locale_path.exists():
                translation = gettext.translation(
                    domain,
                    localedir=str(LOCALES_DIR),
                    languages=[locale],
                    fallback=True,
                )
                self.locales[locale] = translation
            else:
                logger.warning(f"Locale not found: {locale}")

    def gettext(self, locale: str, message: str) -> str:
        """
        Translate a message.

        Args:
            locale: Target locale
            message: Message to translate

        Returns:
            Translated message
        """
        if locale not in self.locales:
            locale = DEFAULT_LOCALE

        translation = self.locales.get(locale)
        if translation:
            return translation.gettext(message)
        return message

    def ngettext(
        self,
        locale: str,
        singular: str,
        plural: str,
        n: int,
    ) -> str:
        """
        Translate a plural message.

        Args:
            locale: Target locale
            singular: Singular form
            plural: Plural form
            n: Count

        Returns:
            Translated plural message
        """
        if locale not in self.locales:
            locale = DEFAULT_LOCALE

        translation = self.locales.get(locale)
        if translation:
            return translation.ngettext(singular, plural, n)
        return singular if n == 1 else plural


# Global i18n instance
i18n = I18n()


def t(message: str, locale: str = DEFAULT_LOCALE) -> str:
    """
    Translate a message.

    Convenience function for translations.

    Args:
        message: Message to translate
        locale: Target locale

    Returns:
        Translated message
    """
    return i18n.gettext(locale, message)


def tn(singular: str, plural: str, n: int, locale: str = DEFAULT_LOCALE) -> str:
    """
    Translate a plural message.

    Args:
        singular: Singular form
        plural: Plural form
        n: Count
        locale: Target locale

    Returns:
        Translated plural message
    """
    return i18n.ngettext(locale, singular, plural, n)


class LocaleMiddleware(I18nMiddleware):
    """
    Middleware for locale selection.

    Determines user locale from database or defaults to 'ru'.
    """

    async def get_user_locale(self, event_from_user, data: dict) -> Optional[str]:
        """
        Get user locale.

        Args:
            event_from_user: User object from event
            data: Event data

        Returns:
            User locale or None for default
        """
        # For now, use language code from Telegram user
        # In production, load from database based on user preferences
        if event_from_user and event_from_user.language_code:
            lang = event_from_user.language_code.split("-")[0]
            if lang in SUPPORTED_LOCALES:
                return lang

        return DEFAULT_LOCALE


def setup_i18n_middleware() -> LocaleMiddleware:
    """
    Setup i18n middleware.

    Returns:
        Configured LocaleMiddleware
    """
    return LocaleMiddleware(
        path=LOCALES_DIR,
        default_locale=DEFAULT_LOCALE,
    )
