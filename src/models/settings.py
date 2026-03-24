"""Settings model for key-value configuration storage."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, String, Text

from src.core.database import Base


class Settings(Base):
    """
    Settings model for dynamic key-value configuration.

    Attributes:
        key: Primary key (setting name)
        value: Setting value
        updated_at: Last update timestamp

    Examples:
        - prices: JSON with subscription prices
        - payment_methods: JSON with enabled payment methods
        - feature_flags: JSON with feature toggles
    """

    __tablename__ = "settings"

    key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Settings(key={self.key}, value={self.value[:50]}...)>"

    @classmethod
    async def get_setting(cls, session, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get setting value by key.

        Args:
            session: Database session
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value or default
        """
        from sqlalchemy import select

        result = await session.execute(
            select(cls).where(cls.key == key)
        )
        setting = result.scalar_one_or_none()
        return setting.value if setting else default

    @classmethod
    async def set_setting(cls, session, key: str, value: str) -> "Settings":
        """
        Set setting value.

        Args:
            session: Database session
            key: Setting key
            value: Setting value

        Returns:
            Updated Settings instance
        """
        from sqlalchemy import select, insert
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        result = await session.execute(
            select(cls).where(cls.key == key)
        )
        setting = result.scalar_one_or_none()

        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
        else:
            # Use SQLite-specific upsert
            stmt = sqlite_insert(cls).values(key=key, value=value)
            stmt = stmt.on_conflict_do_update(
                index_elements=[cls.key],
                set_={"value": value, "updated_at": datetime.utcnow()}
            )
            await session.execute(stmt)
            result = await session.execute(select(cls).where(cls.key == key))
            setting = result.scalar_one()

        return setting
