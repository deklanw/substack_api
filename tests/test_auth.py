import asyncio
import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from curl_cffi import requests as curl_requests

from substack_api.auth import SubstackAuth
from substack_api.post import HEADERS as POST_HEADERS
from substack_api._http import DEFAULT_TIMEOUT


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def temp_cookies_file():
    """Create a temporary file for cookies storage."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def mock_cookies():
    """Mock cookies data."""
    return {
        "substack.sid": {
            "value": "test_session_id",
            "domain": ".substack.com",
            "path": "/",
            "secure": True,
            "expires": None,
        },
        "substack.lli": {
            "value": "test_lli_value",
            "domain": ".substack.com",
            "path": "/",
            "secure": True,
            "expires": None,
        },
    }


@pytest.fixture
def mock_selenium_cookies():
    """Mock cookies returned by Selenium."""
    return [
        {
            "name": "substack.sid",
            "value": "test_session_id",
            "domain": ".substack.com",
            "path": "/",
            "secure": True,
        },
        {
            "name": "substack.lli",
            "value": "test_lli_value",
            "domain": ".substack.com",
            "path": "/",
            "secure": True,
        },
    ]


class TestSubstackAuth:
    """Test cases for SubstackAuth class."""

    def test_init_without_credentials(self, temp_cookies_file):
        auth = SubstackAuth(cookies_path=temp_cookies_file + ".nonexistent")

        try:
            assert auth.cookies_path == temp_cookies_file + ".nonexistent"
            assert not auth.authenticated
            assert isinstance(auth.session, curl_requests.AsyncSession)
        finally:
            run(auth.aclose())

    def test_init_with_existing_cookies(self, temp_cookies_file, mock_cookies):
        with open(temp_cookies_file, "w") as f:
            json.dump(mock_cookies, f)

        with patch.object(SubstackAuth, "load_cookies", return_value=True) as mock_load:
            auth = SubstackAuth(cookies_path=temp_cookies_file)
            try:
                mock_load.assert_called_once()
                assert auth.authenticated
            finally:
                run(auth.aclose())

    def test_load_cookies_file_not_found(self, temp_cookies_file):
        auth = SubstackAuth(cookies_path=temp_cookies_file + ".nonexistent")
        try:
            result = auth.load_cookies()

            assert result is False
            assert not auth.authenticated
        finally:
            run(auth.aclose())

    def test_load_cookies_supports_dict_format(self, temp_cookies_file, mock_cookies):
        with open(temp_cookies_file, "w") as f:
            json.dump(mock_cookies, f)

        auth = SubstackAuth(cookies_path=temp_cookies_file)
        try:
            assert auth.authenticated
            assert auth.session.cookies.get("substack.sid") == "test_session_id"
            assert auth.session.cookies.get("substack.lli") == "test_lli_value"
        finally:
            run(auth.aclose())

    def test_load_cookies_supports_list_format(
        self, temp_cookies_file, mock_selenium_cookies
    ):
        with open(temp_cookies_file, "w") as f:
            json.dump(mock_selenium_cookies, f)

        auth = SubstackAuth(cookies_path=temp_cookies_file)
        try:
            assert auth.authenticated
            assert auth.session.cookies.get("substack.sid") == "test_session_id"
        finally:
            run(auth.aclose())

    def test_get_request(self, temp_cookies_file, mock_cookies):
        with open(temp_cookies_file, "w") as f:
            json.dump(mock_cookies, f)
        auth = SubstackAuth(cookies_path=temp_cookies_file)
        auth.authenticated = True

        mock_response = MagicMock()

        try:
            with patch.object(
                auth.session, "get", new=AsyncMock(return_value=mock_response)
            ) as mock_get:
                result = run(auth.get("https://example.com/api", timeout=30))

                assert result == mock_response
                mock_get.assert_awaited_once_with("https://example.com/api", timeout=30)
        finally:
            run(auth.aclose())

    def test_post_request(self, temp_cookies_file, mock_cookies):
        with open(temp_cookies_file, "w") as f:
            json.dump(mock_cookies, f)
        auth = SubstackAuth(cookies_path=temp_cookies_file)
        auth.authenticated = True

        mock_response = MagicMock()
        data = {"key": "value"}

        try:
            with patch.object(
                auth.session, "post", new=AsyncMock(return_value=mock_response)
            ) as mock_post:
                result = run(auth.post("https://example.com/api", json=data))

                assert result == mock_response
                mock_post.assert_awaited_once_with("https://example.com/api", json=data)
        finally:
            run(auth.aclose())

    def test_session_headers(self, temp_cookies_file, mock_cookies):
        with open(temp_cookies_file, "w") as f:
            json.dump(mock_cookies, f)
        auth = SubstackAuth(cookies_path=temp_cookies_file)

        try:
            assert "User-Agent" in auth.session.headers
            assert auth.session.headers["Accept"] == "application/json"
            assert auth.session.headers["Content-Type"] == "application/json"
        finally:
            run(auth.aclose())


class TestAuthIntegration:
    """Test authentication integration with Post and Newsletter classes."""

    @patch("substack_api.post.async_get", new_callable=AsyncMock)
    def test_post_without_auth(self, mock_get):
        from substack_api.post import Post

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 123,
            "body_html": None,
            "audience": "only_paid",
        }
        mock_get.return_value = mock_response

        post = Post("https://test.substack.com/p/test-post")
        content = run(post.get_content())

        mock_get.assert_awaited_once_with(
            post.endpoint,
            headers=POST_HEADERS,
            timeout=DEFAULT_TIMEOUT,
        )
        assert content is None

    def test_post_with_auth(self, temp_cookies_file, mock_cookies):
        with open(temp_cookies_file, "w") as f:
            json.dump(mock_cookies, f)
        auth = SubstackAuth(cookies_path=temp_cookies_file)
        auth.authenticated = True

        from substack_api.post import Post

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 123,
            "body_html": "<p>Paywalled content</p>",
            "audience": "only_paid",
        }

        try:
            with patch.object(
                auth, "get", new=AsyncMock(return_value=mock_response)
            ) as mock_auth_get:
                post = Post("https://test.substack.com/p/test-post", auth=auth)
                content = run(post.get_content())

                mock_auth_get.assert_awaited_once_with(
                    post.endpoint, timeout=DEFAULT_TIMEOUT
                )
                assert content == "<p>Paywalled content</p>"
        finally:
            run(auth.aclose())

    def test_post_is_paywalled(self):
        from substack_api.post import Post

        post = Post("https://test.substack.com/p/test-post")

        with patch.object(
            post, "_fetch_post_data", new=AsyncMock(return_value={"audience": "only_paid"})
        ):
            assert run(post.is_paywalled()) is True

        with patch.object(
            post, "_fetch_post_data", new=AsyncMock(return_value={"audience": "everyone"})
        ):
            assert run(post.is_paywalled()) is False

    def test_newsletter_with_auth_passes_to_posts(
        self, temp_cookies_file, mock_cookies
    ):
        from substack_api.newsletter import Newsletter
        from substack_api.post import Post

        with open(temp_cookies_file, "w") as f:
            json.dump(mock_cookies, f)
        auth = SubstackAuth(cookies_path=temp_cookies_file)
        auth.authenticated = True

        newsletter = Newsletter("https://test.substack.com", auth=auth)

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"canonical_url": "https://test.substack.com/p/post1"},
            {"canonical_url": "https://test.substack.com/p/post2"},
        ]

        try:
            with patch.object(
                newsletter,
                "_make_request",
                new=AsyncMock(return_value=mock_response),
            ):
                posts = run(newsletter.get_posts(limit=2))

                assert len(posts) == 2
                assert all(isinstance(p, Post) for p in posts)
                assert all(p.auth == auth for p in posts)
        finally:
            run(auth.aclose())
