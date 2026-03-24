"""Application configuration from environment variables."""

import os
from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


def to_snake_case(name: str) -> str:
    """Convert field name to snake case for env variable lookup."""
    return name.lower()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        alias_generator=to_snake_case,
        populate_by_name=True,
    )

    # Telegram Bot
    BOT_TOKEN: str = Field(..., description="Telegram bot token")

    # 3x-ui Panel (RU)
    PANEL_3XUI_URL: str = Field(..., description="3x-ui panel URL")
    PANEL_3XUI_USER: str = Field(..., description="3x-ui admin username")
    PANEL_3XUI_PASS: str = Field(..., description="3x-ui admin password")
    INBOUND_RU_TAG: str = Field(..., description="3x-ui inbound tag")
    SNI_RU: str = Field(..., description="Reality SNI domain")
    PUBLIC_KEY_RU: str = Field(..., description="Reality public key")
    SHORT_ID_RU: str = Field(..., description="Reality short ID")
    SERVER_ADDRESS_RU: str = Field(..., description="RU server IP/domain")
    SERVER_PORT_RU: int = Field(..., description="RU server port")

    # Hiddify Panel (EU)
    PANEL_HIDDIFY_URL: str = Field(..., description="Hiddify panel URL")
    PANEL_HIDDIFY_API_KEY: str = Field(..., description="Hiddify API key")

    # Payments
    CRYPTOMUS_API_KEY: Optional[str] = Field(None, description="Cryptomus API key")
    YOOKASSA_SHOP_ID: Optional[str] = Field(None, description="YooKassa shop ID")
    YOOKASSA_SECRET_KEY: Optional[str] = Field(None, description="YooKassa secret key")

    # Admin
    ADMIN_TELEGRAM_ID: Optional[int] = Field(None, description="Admin Telegram ID")

    # Database
    DATABASE_URL: str = Field("sqlite+aiosqlite:///vpn_bot.db", description="Database connection URL")

    # Defaults
    DEFAULT_TRAFFIC_LIMIT_RU: Optional[int] = Field(None, description="RU traffic limit (bytes)")
    DEFAULT_TRAFFIC_LIMIT_EU: Optional[int] = Field(None, description="EU traffic limit (bytes)")

    # Property aliases for backward compatibility
    @property
    def bot_token(self) -> str:
        return self.BOT_TOKEN

    @property
    def panel_3xui_url(self) -> str:
        return self.PANEL_3XUI_URL

    @property
    def panel_3xui_user(self) -> str:
        return self.PANEL_3XUI_USER

    @property
    def panel_3xui_pass(self) -> str:
        return self.PANEL_3XUI_PASS

    @property
    def inbound_ru_tag(self) -> str:
        return self.INBOUND_RU_TAG

    @property
    def sni_ru(self) -> str:
        return self.SNI_RU

    @property
    def public_key_ru(self) -> str:
        return self.PUBLIC_KEY_RU

    @property
    def short_id_ru(self) -> str:
        return self.SHORT_ID_RU

    @property
    def server_address_ru(self) -> str:
        return self.SERVER_ADDRESS_RU

    @property
    def server_port_ru(self) -> int:
        return self.SERVER_PORT_RU

    @property
    def panel_hiddify_url(self) -> str:
        return self.PANEL_HIDDIFY_URL

    @property
    def panel_hiddify_api_key(self) -> str:
        return self.PANEL_HIDDIFY_API_KEY

    @property
    def cryptomus_api_key(self) -> Optional[str]:
        return self.CRYPTOMUS_API_KEY

    @property
    def yookassa_shop_id(self) -> Optional[str]:
        return self.YOOKASSA_SHOP_ID

    @property
    def yookassa_secret_key(self) -> Optional[str]:
        return self.YOOKASSA_SECRET_KEY

    @property
    def admin_telegram_id(self) -> Optional[int]:
        return self.ADMIN_TELEGRAM_ID

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def default_traffic_limit_ru(self) -> Optional[int]:
        return self.DEFAULT_TRAFFIC_LIMIT_RU

    @property
    def default_traffic_limit_eu(self) -> Optional[int]:
        return self.DEFAULT_TRAFFIC_LIMIT_EU


# Global settings instance
settings = Settings()
