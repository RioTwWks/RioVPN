"""Base service class with retry logic."""

import logging
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

    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        """
        Initialize base service.

        Args:
            base_url: Base URL for the API
            headers: Optional default headers
        """
        self.base_url = base_url.rstrip("/")
        self.default_headers = headers or {}

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
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {**self.default_headers, **kwargs.pop("headers", {})}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.request(method, url, **kwargs) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"API request failed: {method} {url} - " f"Status: {response.status}, Response: {error_text}")
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
