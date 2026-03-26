"""Hiddify-Manager API client for European VPS management."""

import logging
from typing import Any, Dict, List, Optional

from src.core.config import settings
from src.services.base import APIError, BaseService

logger = logging.getLogger(__name__)


class HiddifyService(BaseService):
    """
    Hiddify-Manager API client.

    Handles all interactions with the Hiddify panel for managing
    European VPS users.
    """

    def __init__(self):
        """Initialize Hiddify service with API key authentication."""
        super().__init__(
            base_url=f"{settings.panel_hiddify_url}/api/v2/",
            headers={"Hiddify-API-Key": settings.panel_hiddify_api_key},
            use_proxy=True,  # Use proxy for Hiddify API
            verify_ssl=False,  # Disable SSL verification for self-signed certs
        )

    async def create_user(
        self,
        username: str,
        expiry_time: int,
        traffic_limit: Optional[int] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create new user in Hiddify panel.

        Args:
            username: Unique username for the user
            expiry_time: Expiry timestamp in seconds (Unix timestamp)
            traffic_limit: Traffic limit in bytes (None = unlimited)
            extra_data: Additional user data

        Returns:
            Created user data including UUID and subscription link

        Raises:
            APIError: If user creation fails
        """
        # Hiddify API v2 - try with minimal required fields first
        # Required: username
        # Optional: expiry_time (Unix seconds), data_limit (bytes), enabled, mode
        user_data = {
            "username": username,
            "enabled": True,
        }
        
        # Only add optional fields if they have values
        if expiry_time:
            user_data["expiry_time"] = expiry_time
        if traffic_limit:
            user_data["data_limit"] = traffic_limit

        if extra_data:
            user_data.update(extra_data)

        logger.info(f"Creating Hiddify user: {username}, expiry={expiry_time}, limit={traffic_limit}")
        
        response = await self.post("/admin/user/", json=user_data)
        logger.info(f"Hiddify response: {response}")

        if response.get("status") == "success" or "uuid" in response or "data" in response:
            logger.info(f"User {username} created in Hiddify")
            return response

        raise APIError(f"Failed to create user: {response}")

    async def get_user(self, uuid: str) -> Optional[Dict[str, Any]]:
        """
        Get user information by UUID.

        Args:
            uuid: User UUID

        Returns:
            User information or None if not found
        """
        try:
            response = await self.get(f"/admin/user/{uuid}")
            if response.get("status") == "success" or "uuid" in response:
                return response
            return None
        except APIError as e:
            if e.status_code == 404:
                return None
            raise

    async def update_user(
        self,
        uuid: str,
        expiry_time: Optional[int] = None,
        traffic_limit: Optional[int] = None,
        enabled: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Update user configuration.

        Args:
            uuid: User UUID
            expiry_time: New expiry timestamp
            traffic_limit: New traffic limit
            enabled: Enable/disable user

        Returns:
            Updated user data
        """
        update_data = {}

        if expiry_time is not None:
            update_data["expiry_time"] = expiry_time
        if traffic_limit is not None:
            update_data["data_limit"] = traffic_limit
        if enabled is not None:
            update_data["enabled"] = enabled

        response = await self.put(f"/admin/user/{uuid}", json=update_data)

        if response.get("status") == "success" or "uuid" in response:
            logger.info(f"User {uuid} updated in Hiddify")
            return response

        raise APIError(f"Failed to update user: {response}")

    async def delete_user(self, uuid: str) -> bool:
        """
        Delete user from Hiddify panel.

        Args:
            uuid: User UUID to delete

        Returns:
            True if user deleted successfully
        """
        try:
            response = await self.delete(f"/admin/user/{uuid}")
            if response.get("status") == "success":
                logger.info(f"User {uuid} deleted from Hiddify")
                return True
            raise APIError(f"Failed to delete user: {response}")
        except APIError as e:
            if e.status_code == 404:
                logger.warning(f"User {uuid} not found, nothing to delete")
                return True
            raise

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get list of all users.

        Returns:
            List of user configurations
        """
        response = await self.get("/admin/users/")
        if response.get("status") == "success":
            return response.get("data", [])
        return []

    async def get_user_traffic(self, uuid: str) -> Dict[str, int]:
        """
        Get user traffic statistics.

        Args:
            uuid: User UUID

        Returns:
            Dictionary with traffic usage
        """
        user = await self.get_user(uuid)
        if user:
            return {
                "used": user.get("used_traffic", 0),
                "limit": user.get("data_limit", 0),
                "remaining": user.get("data_limit", 0) - user.get("used_traffic", 0),
            }
        raise APIError(f"User {uuid} not found")

    async def reset_user_traffic(self, uuid: str) -> Dict[str, Any]:
        """
        Reset user traffic counter.

        Args:
            uuid: User UUID

        Returns:
            Updated user data
        """
        return await self.update_user(uuid)

    async def disable_user(self, uuid: str) -> bool:
        """
        Disable user access.

        Args:
            uuid: User UUID

        Returns:
            True if user disabled successfully
        """
        await self.update_user(uuid, enabled=False)
        return True

    async def enable_user(self, uuid: str) -> bool:
        """
        Enable user access.

        Args:
            uuid: User UUID

        Returns:
            True if user enabled successfully
        """
        await self.update_user(uuid, enabled=True)
        return True
