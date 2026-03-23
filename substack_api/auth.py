import json
import os
from collections.abc import Sequence
from typing import Any

from curl_cffi import requests as curl_requests

from substack_api._http import BROWSER_IMPERSONATE, JSON_HEADERS


class SubstackAuth:
    """Handles authentication for Substack API requests."""

    def __init__(
        self,
        cookies_path: str,
    ):
        """
        Initialize authentication handler.

        Parameters
        ----------
        cookies_path : str, optional
            Path to retrieve session cookies from
        """
        self.cookies_path = cookies_path
        self.session = curl_requests.AsyncSession(
            headers=JSON_HEADERS,
            impersonate=BROWSER_IMPERSONATE,
        )
        self.authenticated = False

        # Try to load existing cookies
        if os.path.exists(self.cookies_path):
            self.authenticated = self.load_cookies()
        else:
            print(f"Cookies file not found at {self.cookies_path}. Please log in.")
            self.authenticated = False
            self.session.cookies.clear()

    def load_cookies(self) -> bool:
        """
        Load cookies from file.

        Returns
        -------
        bool
            True if cookies loaded successfully
        """
        try:
            with open(self.cookies_path, "r") as f:
                raw_cookies = json.load(f)

            cookies = self._normalize_cookies(raw_cookies)
            self.session.cookies.clear()

            for cookie in cookies:
                self.session.cookies.set(
                    cookie["name"],
                    cookie["value"],
                    domain=cookie.get("domain"),
                    path=cookie.get("path", "/"),
                )

            return True

        except Exception as e:
            print(f"Failed to load cookies: {str(e)}")
            self.authenticated = False
            self.session.cookies.clear()
            return False

    @staticmethod
    def _normalize_cookies(raw_cookies: Any) -> list[dict[str, Any]]:
        if isinstance(raw_cookies, dict):
            return [
                {"name": name, **cookie_data}
                for name, cookie_data in raw_cookies.items()
                if isinstance(cookie_data, dict)
            ]

        if isinstance(raw_cookies, Sequence) and not isinstance(raw_cookies, (str, bytes)):
            return [
                cookie
                for cookie in raw_cookies
                if isinstance(cookie, dict) and "name" in cookie and "value" in cookie
            ]

        raise ValueError("Cookies file must contain a dict or list of cookie objects")

    async def get(self, url: str, **kwargs) -> curl_requests.Response:
        """
        Make authenticated GET request.

        Parameters
        ----------
        url : str
            URL to request
        **kwargs
            Additional arguments to pass to curl_cffi AsyncSession.get

        Returns
        -------
        curl_cffi.requests.Response
            Response object
        """
        return await self.session.get(url, **kwargs)

    async def post(self, url: str, **kwargs) -> curl_requests.Response:
        """
        Make authenticated POST request.

        Parameters
        ----------
        url : str
            URL to request
        **kwargs
            Additional arguments to pass to curl_cffi AsyncSession.post

        Returns
        -------
        curl_cffi.requests.Response
            Response object
        """
        return await self.session.post(url, **kwargs)

    async def aclose(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> "SubstackAuth":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()
