import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from curl_cffi import requests as curl_requests

from substack_api._http import DEFAULT_TIMEOUT, HEADERS, async_get

# Setup logger
logger = logging.getLogger(__name__)


async def resolve_handle_redirect(
    old_handle: str,
    timeout: float = DEFAULT_TIMEOUT,
    proxy: str | None = None,
) -> Optional[str]:
    """
    Resolve a potentially renamed Substack handle by following redirects.

    Parameters
    ----------
    old_handle : str
        The original handle that may have been renamed
    timeout : int
        Request timeout in seconds
    proxy : str, optional
        Proxy URL used for the redirect lookup

    Returns
    -------
    Optional[str]
        The new handle if renamed, None if no redirect or on error
    """
    try:
        # Make request to the public profile page with redirects enabled
        request_kwargs = {
            "timeout": timeout,
            "allow_redirects": True,
        }
        if proxy is not None:
            request_kwargs["proxy"] = proxy
        response = await async_get(
            f"https://substack.com/@{old_handle}",
            headers=HEADERS,
            **request_kwargs,
        )

        # If we got a successful response, check if we were redirected
        if response.status_code == 200:
            # Parse the final URL to extract the handle
            parsed_url = urlparse(response.url)
            path_parts = parsed_url.path.strip("/").split("/")

            # Check if this is a profile URL (starts with @)
            if path_parts and path_parts[0].startswith("@"):
                new_handle = path_parts[0][1:]  # Remove the @ prefix

                # Only return if it's actually different
                if new_handle and new_handle != old_handle:
                    logger.info(
                        f"Handle redirect detected: {old_handle} -> {new_handle}"
                    )
                    return new_handle

        return None

    except curl_requests.exceptions.RequestException as e:
        logger.debug(f"Error resolving handle redirect for {old_handle}: {e}")
        return None


class User:
    """
    User class for interacting with Substack user profiles.

    Now handles renamed accounts by following redirects when a handle has changed.
    """

    def __init__(
        self,
        username: str,
        follow_redirects: bool = True,
        proxy: str | None = None,
    ):
        """
        Initialize a User object.

        Parameters
        ----------
        username : str
            The Substack username
        follow_redirects : bool
            Whether to follow redirects when a handle has been renamed (default: True)
        proxy : str, optional
            Proxy URL used for requests
        """
        self.username = username
        self.original_username = username  # Keep track of the original
        self.follow_redirects = follow_redirects
        self.proxy = proxy
        self.endpoint = f"https://substack.com/api/v1/user/{username}/public_profile"
        self._user_data = None  # Cache for user data
        self._redirect_attempted = False  # Prevent infinite redirect loops

    def __str__(self) -> str:
        return f"User: {self.username}"

    def __repr__(self) -> str:
        return f"User(username={self.username})"

    def _update_handle(self, new_handle: str) -> None:
        """
        Update the user's handle and endpoint.

        Parameters
        ----------
        new_handle : str
            The new handle after redirect
        """
        logger.info(f"Updating handle from {self.username} to {new_handle}")
        self.username = new_handle
        self.endpoint = f"https://substack.com/api/v1/user/{new_handle}/public_profile"

    async def _fetch_user_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetch the raw user data from the API and cache it.

        Handles renamed accounts by following redirects when follow_redirects is True.

        Parameters
        ----------
        force_refresh : bool
            Whether to force a refresh of the data, ignoring the cache

        Returns
        -------
        Dict[str, Any]
            Full user profile data

        Raises
        ------
        curl_cffi.requests.exceptions.HTTPError
            If the user cannot be found even after redirect attempts
        """
        if self._user_data is not None and not force_refresh:
            return self._user_data

        try:
            request_kwargs = {"timeout": DEFAULT_TIMEOUT}
            if self.proxy is not None:
                request_kwargs["proxy"] = self.proxy
            r = await async_get(self.endpoint, headers=HEADERS, **request_kwargs)
            r.raise_for_status()
            self._user_data = r.json()
            return self._user_data

        except curl_requests.exceptions.HTTPError as e:
            # Handle 404 errors if we should follow redirects
            if (
                e.response.status_code == 404
                and self.follow_redirects
                and not self._redirect_attempted
            ):
                # Mark that we've attempted a redirect to prevent loops
                self._redirect_attempted = True

                # Try to resolve the redirect
                resolve_kwargs = {}
                if self.proxy is not None:
                    resolve_kwargs["proxy"] = self.proxy
                new_handle = await resolve_handle_redirect(self.username, **resolve_kwargs)

                if new_handle:
                    # Update our state with the new handle
                    self._update_handle(new_handle)

                    # Try the request again with the new handle
                    try:
                        request_kwargs = {"timeout": DEFAULT_TIMEOUT}
                        if self.proxy is not None:
                            request_kwargs["proxy"] = self.proxy
                        r = await async_get(self.endpoint, headers=HEADERS, **request_kwargs)
                        r.raise_for_status()
                        self._user_data = r.json()
                        return self._user_data
                    except curl_requests.exceptions.HTTPError:
                        # If it still fails, log and re-raise
                        logger.error(
                            f"Failed to fetch user data even after redirect to {new_handle}"
                        )
                        raise
                else:
                    # No redirect found, this is a real 404
                    logger.debug(
                        f"No redirect found for {self.username}, user may be deleted"
                    )

            # Re-raise the original error
            raise

    async def get_raw_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get the complete raw user data.

        Parameters
        ----------
        force_refresh : bool
            Whether to force a refresh of the data, ignoring the cache

        Returns
        -------
        Dict[str, Any]
            Full user profile data
        """
        return await self._fetch_user_data(force_refresh=force_refresh)

    def _require_user_data(self) -> Dict[str, Any]:
        if self._user_data is None:
            raise RuntimeError("User data has not been loaded. Await get_raw_data() first.")
        return self._user_data

    @property
    def id(self) -> int:
        """
        Get the user's unique ID number

        Returns
        -------
        int
            The user's ID
        """
        data = self._require_user_data()
        return data["id"]

    @property
    def name(self) -> str:
        """
        Get the user's name

        Returns
        -------
        str
            The user's name
        """
        data = self._require_user_data()
        return data["name"]

    @property
    def profile_set_up_at(self) -> str:
        """
        Get the date when the user's profile was set up

        Returns
        -------
        str
            Profile setup timestamp
        """
        data = self._require_user_data()
        return data["profile_set_up_at"]

    @property
    def was_redirected(self) -> bool:
        """
        Check if this user's handle was redirected from the original.

        Returns
        -------
        bool
            True if the handle was changed via redirect
        """
        return self.username != self.original_username

    async def get_subscriptions(self) -> List[Dict[str, Any]]:
        """
        Get newsletters the user has subscribed to

        Returns
        -------
        List[Dict[str, Any]]
            List of publications the user subscribes to with domain info
        """
        data = await self._fetch_user_data()
        subscriptions = []

        for sub in data.get("subscriptions", []):
            pub = sub["publication"]
            domain = pub.get("custom_domain") or f"{pub['subdomain']}.substack.com"
            subscriptions.append(
                {
                    "publication_id": pub["id"],
                    "publication_name": pub["name"],
                    "domain": domain,
                    "membership_state": sub["membership_state"],
                }
            )

        return subscriptions
