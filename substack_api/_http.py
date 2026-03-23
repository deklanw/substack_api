import asyncio
from typing import Any, Mapping

from curl_cffi import requests as curl_requests

DEFAULT_TIMEOUT = 30.0
REQUEST_DELAY_SECONDS = 2.0
BROWSER_IMPERSONATE = "chrome"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36"
}

JSON_HEADERS = {
    **HEADERS,
    "Accept": "application/json",
    "Content-Type": "application/json",
}


async def async_get(
    url: str,
    *,
    client: curl_requests.AsyncSession | None = None,
    headers: Mapping[str, str] | None = None,
    **kwargs: Any,
) -> curl_requests.Response:
    if client is not None:
        request_kwargs = dict(kwargs)
        if headers is not None:
            request_kwargs["headers"] = headers
        return await client.get(url, **request_kwargs)

    async with curl_requests.AsyncSession(
        headers=headers or HEADERS,
        impersonate=BROWSER_IMPERSONATE,
    ) as temp_client:
        return await temp_client.get(url, **kwargs)


async def async_post(
    url: str,
    *,
    client: curl_requests.AsyncSession | None = None,
    headers: Mapping[str, str] | None = None,
    **kwargs: Any,
) -> curl_requests.Response:
    if client is not None:
        request_kwargs = dict(kwargs)
        if headers is not None:
            request_kwargs["headers"] = headers
        return await client.post(url, **request_kwargs)

    async with curl_requests.AsyncSession(
        headers=headers or JSON_HEADERS,
        impersonate=BROWSER_IMPERSONATE,
    ) as temp_client:
        return await temp_client.post(url, **kwargs)


async def polite_request_delay() -> None:
    await asyncio.sleep(REQUEST_DELAY_SECONDS)
