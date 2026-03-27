"""Base service class with retry logic."""

import logging
import ssl
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import aiohttp
from aiohttp import ClientError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Base exception for service errors."""

    pass


class APIError(ServiceError):
    """Exception for API-related errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        """
        Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code if available
        """
        super().__init__(message)
        self.status_code = status_code


class BaseService(ABC):
    """
    Base class for all external API services.

    Provides retry logic, session management, and common HTTP methods.
    """

    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        use_proxy: bool = True,
        verify_ssl: bool = False,
        auth: Optional[aiohttp.BasicAuth] = None,
    ):
        """
        Initialize base service.

        Args:
            base_url: Base URL for the API
            headers: Optional default headers
            use_proxy: Use proxy for connections (default True)
            verify_ssl: Verify SSL certificates (default False for self-signed certs)
            auth: Optional aiohttp.BasicAuth for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.default_headers = headers or {}
        self.use_proxy = use_proxy
        self.verify_ssl = verify_ssl
        self.auth = auth

    def _get_connector(self) -> Optional[aiohttp.TCPConnector]:
        """
        Get TCP connector with proxy and SSL settings.

        Returns:
            TCPConnector or None for default
        """
        if not self.use_proxy:
            # No proxy - just disable SSL verification if needed
            if not self.verify_ssl:
                connector = aiohttp.TCPConnector(ssl=False)
                return connector
            return None

        # Use proxy with SSL disabled
        from aiohttp_socks import ProxyConnector

        proxy_url = self._get_proxy_url()
        if not proxy_url:
            return None

        try:
            if self.verify_ssl:
                connector = ProxyConnector.from_url(proxy_url)
            else:
                # Disable SSL verification
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                connector = ProxyConnector.from_url(proxy_url, ssl=ssl_context)
            return connector
        except ImportError:
            logger.warning("aiohttp_socks not installed, using direct connection")
            return None

    def _get_proxy_url(self) -> Optional[str]:
        """
        Get proxy URL from settings.

        Returns:
            Proxy URL or None
        """
        from src.core.config import settings

        if settings.proxy_mode == "direct":
            return None

        # For ssh_tunnel and socks5 modes, use the proxy URL
        if settings.proxy_url:
            return settings.proxy_url

        return None

    def _get_retry_decorator(self):
        """
        Get retry decorator for API calls.

        Returns:
            Retry decorator with exponential backoff
        """
        return retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((ClientError, aiohttp.ClientConnectionError)),
            reraise=True,
        )

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (appended to base_url)
            **kwargs: Additional arguments for aiohttp request

        Returns:
            JSON response as dictionary

        Raises:
            APIError: If request fails
        """
        # Join URLs properly - handle both absolute and relative endpoints
        if endpoint.startswith(("http://", "https://")):
            url = endpoint
        elif endpoint.startswith("/"):
            url = f"{self.base_url}{endpoint}"
        else:
            url = f"{self.base_url}/{endpoint}"

        headers = {**self.default_headers, **kwargs.pop("headers", {})}

        connector = self._get_connector()

        # Prepare auth
        auth = kwargs.pop("auth", self.auth)

        async with aiohttp.ClientSession(headers=headers, connector=connector, auth=auth) as session:
            async with session.request(method, url, **kwargs) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"API request failed: {method} {url} - Status: {response.status}, Response: {error_text}")

                    # Try to parse and log detailed error from JSON
                    try:
                        import json

                        error_json = json.loads(error_text)
                        logger.error(f"Error details: {error_json}")
                        # Hiddify API often returns 'data' with validation errors
                        if "data" in error_json:
                            logger.error(f"Validation errors: {error_json.get('data', {})}")
                    except Exception as e:
                        logger.debug(f"Could not parse error JSON: {e}")

                    raise APIError(
                        f"API request failed with status {response.status}: {error_text}",
                        status_code=response.status,
                    )

                return await response.json()

    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make GET request.

        Args:
            endpoint: API endpoint
            **kwargs: Additional request arguments

        Returns:
            JSON response
        """
        return await self._request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make POST request.

        Args:
            endpoint: API endpoint
            **kwargs: Additional request arguments

        Returns:
            JSON response
        """
        return await self._request("POST", endpoint, **kwargs)

    async def put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make PUT request.

        Args:
            endpoint: API endpoint
            **kwargs: Additional request arguments

        Returns:
            JSON response
        """
        return await self._request("PUT", endpoint, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make DELETE request.

        Args:
            endpoint: API endpoint
            **kwargs: Additional request arguments

        Returns:
            JSON response
        """
        return await self._request("DELETE", endpoint, **kwargs)
