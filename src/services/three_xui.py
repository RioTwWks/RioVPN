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
        super().__init__(
            base_url=settings.panel_3xui_url,
            headers={"Content-Type": "application/json"},
        )
        self.username = settings.panel_3xui_user
        self.password = settings.panel_3xui_pass
        self._session_cookies: Optional[aiohttp.CookieJar] = None

    async def login(self) -> bool:
        """
        Authenticate with 3x-ui panel using session-based auth.

        Returns:
            True if authentication successful

        Raises:
            APIError: If authentication fails
        """
        try:
            # Create cookie jar for session
            self._session_cookies = aiohttp.CookieJar()

            # Get connector with proxy support
            connector = self._get_session_connector()

            async with aiohttp.ClientSession(cookie_jar=self._session_cookies, connector=connector) as session:
                # 3x-ui uses POST to /login with JSON body
                login_data = {
                    "username": self.username,
                    "password": self.password,
                }

                async with session.post(
                    f"{self.base_url}/login", json=login_data, ssl=False  # Disable SSL verification for self-signed certs
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get("success"):
                            logger.info("3x-ui login successful")
                            return True

                    error_text = await resp.text()
                    logger.error(f"3x-ui login failed: {resp.status} - {error_text}")
                    raise APIError(f"Login failed: {resp.status}", resp.status)

        except aiohttp.ClientError as e:
            raise APIError(f"Connection error: {e}")

    def _get_session_connector(self):
        """Get connector for session-based requests."""
        if self.use_proxy:
            from aiohttp_socks import ProxyConnector

            proxy_url = self._get_proxy_url()
            if proxy_url:
                import ssl

                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                return ProxyConnector.from_url(proxy_url, ssl=ssl_context)

        return aiohttp.TCPConnector(ssl=False)

    async def _api_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make API request with session authentication.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request arguments

        Returns:
            JSON response

        Raises:
            APIError: If request fails
        """
        # Ensure we're logged in
        if self._session_cookies is None:
            await self.login()

        connector = self._get_session_connector()
        url = f"{self.base_url}{endpoint}"

        async with aiohttp.ClientSession(
            connector=connector, cookie_jar=self._session_cookies, headers=self.default_headers
        ) as session:
            async with session.request(method, url, ssl=False, **kwargs) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(f"API request failed: {method} {endpoint} - {resp.status} - {error_text}")
                    raise APIError(f"API request failed: {resp.status}", resp.status)

                return await resp.json()

    async def get_inbounds(self) -> List[Dict[str, Any]]:
        """
        Get list of all inbounds and clients.

        Returns:
            List of inbound configurations with clients
        """
        response = await self._api_request("GET", "/panel/api/inbounds/list")
        # Handle both dict and string responses
        if isinstance(response, str):
            import json
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                raise APIError(f"Invalid JSON response from get_inbounds: {response}")

        if not response.get("success"):
            raise APIError("Failed to get inbounds")
        
        # Get obj which should be a list of inbounds
        obj = response.get("obj", [])
        
        # Parse each inbound if it's a string
        inbounds = []
        for inbound in obj:
            if isinstance(inbound, str):
                try:
                    import json
                    inbound = json.loads(inbound)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse inbound as JSON: {inbound}")
                    continue
            inbounds.append(inbound)
        
        return inbounds

    async def get_inbound_by_tag(self, tag: str) -> Optional[Dict[str, Any]]:
        """
        Get inbound configuration by tag (or remark).

        Args:
            tag: Inbound tag or remark to search for

        Returns:
            Inbound configuration or None if not found
        """
        inbounds = await self.get_inbounds()
        for inbound in inbounds:
            # Try to match by tag first, then by remark
            if inbound.get("tag") == tag or inbound.get("remark") == tag:
                return inbound
        return None

    async def add_client(
        self,
        inbound_id: int,
        email: str,
        uuid: str,
        traffic_limit: Optional[int] = None,
        expiry_time: Optional[int] = None,
        telegram_id: Optional[int] = None,
    ) -> bool:
        """
        Add client to existing inbound.

        Args:
            inbound_id: ID of the inbound to add client to
            email: Client email (used as identifier)
            uuid: Client UUID for VLESS
            traffic_limit: Traffic limit in bytes (None = unlimited)
            expiry_time: Expiry timestamp in milliseconds (None = unlimited)
            telegram_id: Telegram user ID (optional, for tracking)

        Returns:
            True if client added successfully

        Raises:
            APIError: If adding client fails
        """
        import json

        # 3x-ui expects settings as a JSON string, not object
        client_config = {
            "id": inbound_id,
            "settings": json.dumps(
                {
                    "clients": [
                        {
                            "id": uuid,
                            "email": email,
                            "limitIp": 0,
                            "totalGB": traffic_limit or 0,
                            "expiryTime": expiry_time or 0,
                            "enable": True,
                            "tgId": telegram_id or "",
                            "subId": "",
                        }
                    ]
                }
            ),
        }

        response = await self._api_request("POST", "/panel/api/inbounds/addClient", json=client_config)
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

                    response = await self._api_request("POST", "/panel/api/inbounds/delClient", json=delete_config)
                    # Handle both dict and string responses
                    if isinstance(response, str):
                        import json
                        try:
                            response = json.loads(response)
                        except json.JSONDecodeError:
                            logger.info(f"Client {email} deleted from inbound {client_id} (response: {response})")
                            return True
                    
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
