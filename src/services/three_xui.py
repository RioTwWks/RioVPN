"""3x-ui panel API client for Russian VPS management."""

import logging
from typing import Any, Dict, List, Optional

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings
from src.services.base import APIError, BaseService

logger = logging.getLogger(__name__)


class ThreeXuiService(BaseService):
    """
    3x-ui panel API client.

    Handles all interactions with the 3x-ui panel for managing
    Russian VPS clients (VLESS + Reality + XHTTP).
    """

    def __init__(self):
        """Initialize 3x-ui service with authentication."""
        self.auth = aiohttp.BasicAuth(
            login=settings.panel_3xui_user,
            password=settings.panel_3xui_pass,
        )
        super().__init__(
            base_url=settings.panel_3xui_url,
            headers={"Content-Type": "application/json"},
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def login(self) -> bool:
        """
        Authenticate with 3x-ui panel.

        Returns:
            True if authentication successful

        Raises:
            APIError: If authentication fails
        """
        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                async with session.get(f"{self.base_url}/panel/api/inbounds/list") as resp:
                    if resp.status == 200:
                        return True
                    raise APIError(f"Authentication failed: {resp.status}", resp.status)
        except aiohttp.ClientError as e:
            raise APIError(f"Connection error: {e}")

    async def get_inbounds(self) -> List[Dict[str, Any]]:
        """
        Get list of all inbounds and clients.

        Returns:
            List of inbound configurations with clients
        """
        response = await self.get("/panel/api/inbounds/list")
        if response.get("success"):
            return response.get("obj", [])
        raise APIError("Failed to get inbounds")

    async def get_inbound_by_tag(self, tag: str) -> Optional[Dict[str, Any]]:
        """
        Get inbound configuration by tag.

        Args:
            tag: Inbound tag to search for

        Returns:
            Inbound configuration or None if not found
        """
        inbounds = await self.get_inbounds()
        for inbound in inbounds:
            if inbound.get("tag") == tag:
                return inbound
        return None

    async def add_client(
        self,
        inbound_id: int,
        email: str,
        uuid: str,
        traffic_limit: Optional[int] = None,
        expiry_time: Optional[int] = None,
    ) -> bool:
        """
        Add client to existing inbound.

        Args:
            inbound_id: ID of the inbound to add client to
            email: Client email (used as identifier)
            uuid: Client UUID for VLESS
            traffic_limit: Traffic limit in bytes (None = unlimited)
            expiry_time: Expiry timestamp in milliseconds (None = unlimited)

        Returns:
            True if client added successfully

        Raises:
            APIError: If adding client fails
        """
        client_config = {
            "id": inbound_id,
            "settings": {
                "clients": [
                    {
                        "id": uuid,
                        "email": email,
                        "limitIp": 0,
                        "totalGB": traffic_limit or 0,
                        "expiryTime": expiry_time or 0,
                        "enable": True,
                        "tgId": "",
                        "subId": "",
                    }
                ]
            },
        }

        response = await self.post("/panel/api/inbounds/addClient", json=client_config)
        if response.get("success"):
            logger.info(f"Client {email} added to inbound {inbound_id}")
            return True
        raise APIError(f"Failed to add client: {response.get('msg', 'Unknown error')}")

    async def update_client(
        self,
        email: str,
        traffic_limit: Optional[int] = None,
        expiry_time: Optional[int] = None,
    ) -> bool:
        """
        Update client limits.

        Args:
            email: Client email
            traffic_limit: New traffic limit in bytes
            expiry_time: New expiry timestamp in milliseconds

        Returns:
            True if client updated successfully
        """
        inbounds = await self.get_inbounds()

        for inbound in inbounds:
            clients = inbound.get("settings", {}).get("clients", [])
            for client in clients:
                if client.get("email") == email:
                    client_id = inbound.get("id")
                    uuid = client.get("id")
                    return await self.add_client(
                        inbound_id=client_id,
                        email=email,
                        uuid=uuid,
                        traffic_limit=traffic_limit,
                        expiry_time=expiry_time,
                    )

        raise APIError(f"Client {email} not found")

    async def delete_client(self, email: str) -> bool:
        """
        Delete client from panel.

        Args:
            email: Client email to delete

        Returns:
            True if client deleted successfully
        """
        inbounds = await self.get_inbounds()

        for inbound in inbounds:
            clients = inbound.get("settings", {}).get("clients", [])
            for client in clients:
                if client.get("email") == email:
                    client_id = inbound.get("id")
                    client_uuid = client.get("id")

                    delete_config = {
                        "id": client_id,
                        "clientId": client_uuid,
                    }

                    response = await self.post(
                        "/panel/api/inbounds/delClient", json=delete_config
                    )
                    if response.get("success"):
                        logger.info(f"Client {email} deleted from inbound {client_id}")
                        return True
                    raise APIError(f"Failed to delete client: {response.get('msg')}")

        raise APIError(f"Client {email} not found")

    async def get_client_traffic(self, email: str) -> Dict[str, int]:
        """
        Get client traffic statistics.

        Args:
            email: Client email

        Returns:
            Dictionary with 'up' and 'down' traffic in bytes
        """
        inbounds = await self.get_inbounds()

        for inbound in inbounds:
            clients = inbound.get("settings", {}).get("clients", [])
            for client in clients:
                if client.get("email") == email:
                    return {
                        "up": client.get("up", 0),
                        "down": client.get("down", 0),
                        "total": client.get("up", 0) + client.get("down", 0),
                    }

        raise APIError(f"Client {email} not found")

    async def get_client_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get client configuration by email.

        Args:
            email: Client email

        Returns:
            Client configuration or None if not found
        """
        inbounds = await self.get_inbounds()

        for inbound in inbounds:
            clients = inbound.get("settings", {}).get("clients", [])
            for client in clients:
                if client.get("email") == email:
                    return {
                        **client,
                        "inbound_id": inbound.get("id"),
                        "inbound_tag": inbound.get("tag"),
                    }

        return None
