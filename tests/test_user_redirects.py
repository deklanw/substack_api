import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from curl_cffi import requests as curl_requests

from substack_api.user import HEADERS, User, resolve_handle_redirect


def run(coro):
    return asyncio.run(coro)


def make_http_status_error(status_code: int) -> curl_requests.exceptions.HTTPError:
    response = curl_requests.Response(None)
    response.status_code = status_code
    return curl_requests.exceptions.HTTPError(f"{status_code} error", response=response)


class TestHandleRedirects:
    @patch("substack_api.user.async_get", new_callable=AsyncMock)
    def test_resolve_handle_redirect_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://substack.com/@newhandle"
        mock_get.return_value = mock_response

        result = run(resolve_handle_redirect("oldhandle"))

        assert result == "newhandle"
        mock_get.assert_awaited_once_with(
            "https://substack.com/@oldhandle",
            headers=HEADERS,
            timeout=30.0,
            allow_redirects=True,
        )

    @patch("substack_api.user.async_get", new_callable=AsyncMock)
    def test_resolve_handle_redirect_no_redirect(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://substack.com/@samehandle"
        mock_get.return_value = mock_response

        result = run(resolve_handle_redirect("samehandle"))

        assert result is None

    @patch("substack_api.user.async_get", new_callable=AsyncMock)
    def test_resolve_handle_redirect_error(self, mock_get):
        mock_get.side_effect = curl_requests.exceptions.RequestException("Network error")

        result = run(resolve_handle_redirect("errorhandle"))

        assert result is None

    @patch("substack_api.user.async_get", new_callable=AsyncMock)
    def test_resolve_handle_redirect_404(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = run(resolve_handle_redirect("deletedhandle"))

        assert result is None

    @patch("substack_api.user.async_get", new_callable=AsyncMock)
    def test_resolve_handle_redirect_with_proxy(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://substack.com/@newhandle"
        mock_get.return_value = mock_response

        result = run(
            resolve_handle_redirect(
                "oldhandle",
                proxy="http://127.0.0.1:8080",
            )
        )

        assert result == "newhandle"
        mock_get.assert_awaited_once_with(
            "https://substack.com/@oldhandle",
            headers=HEADERS,
            proxy="http://127.0.0.1:8080",
            timeout=30.0,
            allow_redirects=True,
        )


class TestUserWithRedirects:
    def test_user_init_with_redirects(self):
        user = User("testuser", follow_redirects=True)

        assert user.username == "testuser"
        assert user.original_username == "testuser"
        assert user.follow_redirects is True
        assert user._redirect_attempted is False

    def test_user_init_without_redirects(self):
        user = User("testuser", follow_redirects=False)
        assert user.follow_redirects is False

    @patch("substack_api.user.async_get", new_callable=AsyncMock)
    def test_fetch_user_data_no_redirect_needed(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 123, "name": "Test User"}
        mock_get.return_value = mock_response

        user = User("testuser")
        data = run(user._fetch_user_data())

        assert data == {"id": 123, "name": "Test User"}
        assert user.username == "testuser"
        assert not user.was_redirected
        mock_get.assert_awaited_once()

    @patch("substack_api.user.resolve_handle_redirect", new_callable=AsyncMock)
    @patch("substack_api.user.async_get", new_callable=AsyncMock)
    def test_fetch_user_data_with_redirect(self, mock_get, mock_resolve):
        mock_404 = MagicMock()
        mock_404.status_code = 404
        mock_404.raise_for_status.side_effect = make_http_status_error(404)

        mock_success = MagicMock()
        mock_success.status_code = 200
        mock_success.json.return_value = {
            "id": 123,
            "name": "Test User",
            "handle": "newhandle",
        }

        mock_get.side_effect = [mock_404, mock_success]
        mock_resolve.return_value = "newhandle"

        user = User("oldhandle", follow_redirects=True)
        data = run(user._fetch_user_data())

        assert data == {"id": 123, "name": "Test User", "handle": "newhandle"}
        assert user.username == "newhandle"
        assert user.original_username == "oldhandle"
        assert user.was_redirected
        assert user._redirect_attempted is True
        assert mock_get.await_count == 2
        mock_resolve.assert_awaited_once_with("oldhandle")

    @patch("substack_api.user.resolve_handle_redirect", new_callable=AsyncMock)
    @patch("substack_api.user.async_get", new_callable=AsyncMock)
    def test_fetch_user_data_redirect_disabled(self, mock_get, mock_resolve):
        mock_404 = MagicMock()
        mock_404.status_code = 404
        mock_404.raise_for_status.side_effect = make_http_status_error(404)
        mock_get.return_value = mock_404

        user = User("oldhandle", follow_redirects=False)

        with pytest.raises(curl_requests.exceptions.HTTPError):
            run(user._fetch_user_data())

        mock_resolve.assert_not_awaited()
        assert user.username == "oldhandle"

    @patch("substack_api.user.resolve_handle_redirect", new_callable=AsyncMock)
    @patch("substack_api.user.async_get", new_callable=AsyncMock)
    def test_fetch_user_data_no_redirect_found(self, mock_get, mock_resolve):
        mock_404 = MagicMock()
        mock_404.status_code = 404
        mock_404.raise_for_status.side_effect = make_http_status_error(404)
        mock_get.return_value = mock_404
        mock_resolve.return_value = None

        user = User("deleteduser", follow_redirects=True)

        with pytest.raises(curl_requests.exceptions.HTTPError):
            run(user._fetch_user_data())

        mock_resolve.assert_awaited_once_with("deleteduser")
        assert user.username == "deleteduser"

    @patch("substack_api.user.resolve_handle_redirect", new_callable=AsyncMock)
    @patch("substack_api.user.async_get", new_callable=AsyncMock)
    def test_fetch_user_data_redirect_still_404(self, mock_get, mock_resolve):
        mock_old_404 = MagicMock()
        mock_old_404.status_code = 404
        mock_old_404.raise_for_status.side_effect = make_http_status_error(404)

        mock_new_404 = MagicMock()
        mock_new_404.status_code = 404
        mock_new_404.raise_for_status.side_effect = make_http_status_error(404)

        mock_get.side_effect = [mock_old_404, mock_new_404]
        mock_resolve.return_value = "newhandle"

        user = User("oldhandle", follow_redirects=True)

        with pytest.raises(curl_requests.exceptions.HTTPError):
            run(user._fetch_user_data())

        assert user.username == "newhandle"
        assert user.was_redirected
        assert mock_get.await_count == 2

    @patch("substack_api.user.resolve_handle_redirect", new_callable=AsyncMock)
    @patch("substack_api.user.async_get", new_callable=AsyncMock)
    def test_prevent_infinite_redirect_loop(self, mock_get, mock_resolve):
        mock_404 = MagicMock()
        mock_404.status_code = 404
        mock_404.raise_for_status.side_effect = make_http_status_error(404)
        mock_get.return_value = mock_404
        mock_resolve.return_value = None

        user = User("testuser", follow_redirects=True)

        with pytest.raises(curl_requests.exceptions.HTTPError):
            run(user._fetch_user_data())

        with pytest.raises(curl_requests.exceptions.HTTPError):
            run(user._fetch_user_data())

        assert mock_get.await_count == 2
        mock_resolve.assert_awaited_once_with("testuser")

    def test_update_handle(self):
        user = User("oldhandle")

        user._update_handle("newhandle")

        assert user.username == "newhandle"
        assert user.endpoint == "https://substack.com/api/v1/user/newhandle/public_profile"
        assert user.original_username == "oldhandle"

    def test_was_redirected_property(self):
        user = User("testuser")
        assert not user.was_redirected

        user._update_handle("newhandle")
        assert user.was_redirected


class TestUserRedirectExamples:
    @patch("substack_api.user.resolve_handle_redirect", new_callable=AsyncMock)
    @patch("substack_api.user.async_get", new_callable=AsyncMock)
    def test_real_world_redirects(self, mock_get, mock_resolve):
        test_cases = [
            ("150wordreviews", "johndevore"),
            ("15thcfeminist", "15thcenturyfeminist"),
            ("300tangpoems", "hyunwookimwriter"),
            ("5thingsyoushouldbuy", "beckymalinsky"),
        ]

        for old_handle, new_handle in test_cases:
            mock_404 = MagicMock()
            mock_404.status_code = 404
            mock_404.raise_for_status.side_effect = make_http_status_error(404)

            mock_success = MagicMock()
            mock_success.status_code = 200
            mock_success.json.return_value = {
                "id": 123,
                "handle": new_handle,
                "name": "Test User",
            }

            mock_get.reset_mock()
            mock_resolve.reset_mock()
            mock_get.side_effect = [mock_404, mock_success]
            mock_resolve.return_value = new_handle

            user = User(old_handle)
            data = run(user.get_raw_data())

            assert user.original_username == old_handle
            assert user.username == new_handle
            assert user.was_redirected
            assert data["handle"] == new_handle
