import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from substack_api._http import DEFAULT_TIMEOUT
from substack_api.user import HEADERS, User


def run(coro):
    return asyncio.run(coro)


def test_user_init():
    user = User("testuser")
    assert user.username == "testuser"
    assert user.endpoint == "https://substack.com/api/v1/user/testuser/public_profile"
    assert user._user_data is None


def test_user_string_representation():
    user = User("testuser")
    assert str(user) == "User: testuser"
    assert repr(user) == "User(username=testuser)"


@patch("substack_api.user.async_get", new_callable=AsyncMock)
def test_fetch_user_data(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 123, "name": "Test User"}
    mock_get.return_value = mock_response

    user = User("testuser")
    data = run(user._fetch_user_data())

    assert data == {"id": 123, "name": "Test User"}
    mock_get.assert_awaited_once_with(
        "https://substack.com/api/v1/user/testuser/public_profile",
        headers=HEADERS,
        timeout=DEFAULT_TIMEOUT,
    )


@patch("substack_api.user.async_get", new_callable=AsyncMock)
def test_fetch_user_data_with_proxy(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 123, "name": "Test User"}
    mock_get.return_value = mock_response

    user = User("testuser", proxy="http://127.0.0.1:8080")
    run(user._fetch_user_data())

    mock_get.assert_awaited_once_with(
        "https://substack.com/api/v1/user/testuser/public_profile",
        headers=HEADERS,
        proxy="http://127.0.0.1:8080",
        timeout=DEFAULT_TIMEOUT,
    )


@patch("substack_api.user.async_get", new_callable=AsyncMock)
def test_fetch_user_data_uses_cache(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 123, "name": "Test User"}
    mock_get.return_value = mock_response

    user = User("testuser")
    run(user._fetch_user_data())
    run(user._fetch_user_data())

    mock_get.assert_awaited_once()


@patch("substack_api.user.async_get", new_callable=AsyncMock)
def test_fetch_user_data_force_refresh(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 123, "name": "Test User"}
    mock_get.return_value = mock_response

    user = User("testuser")
    run(user._fetch_user_data())
    run(user._fetch_user_data(force_refresh=True))

    assert mock_get.await_count == 2


@patch("substack_api.user.async_get", new_callable=AsyncMock)
def test_get_raw_data(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 123, "name": "Test User"}
    mock_get.return_value = mock_response

    user = User("testuser")
    data = run(user.get_raw_data())

    assert data == {"id": 123, "name": "Test User"}
    mock_get.assert_awaited_once()


def test_user_id_property_requires_loaded_data():
    user = User("testuser")

    with pytest.raises(RuntimeError, match="Await get_raw_data\\(\\) first"):
        _ = user.id


def test_user_id_property():
    user = User("testuser")
    user._user_data = {"id": 456, "name": "Test User"}

    assert user.id == 456


def test_user_name_property():
    user = User("testuser")
    user._user_data = {"id": 123, "name": "John Doe"}

    assert user.name == "John Doe"


def test_user_profile_setup_date():
    user = User("testuser")
    user._user_data = {
        "id": 123,
        "name": "Test User",
        "profile_set_up_at": "2023-01-01T12:00:00Z",
    }

    assert user.profile_set_up_at == "2023-01-01T12:00:00Z"


@patch("substack_api.user.User._fetch_user_data", new_callable=AsyncMock)
def test_get_subscriptions(mock_fetch):
    mock_fetch.return_value = {
        "subscriptions": [
            {
                "publication": {
                    "id": "123",
                    "name": "Tech Newsletter",
                    "subdomain": "tech",
                },
                "membership_state": "subscribed",
            },
            {
                "publication": {
                    "id": "456",
                    "name": "Science Weekly",
                    "custom_domain": "science-weekly.com",
                },
                "membership_state": "paid_subscriber",
            },
        ]
    }

    user = User("testuser")
    subscriptions = run(user.get_subscriptions())

    expected = [
        {
            "publication_id": "123",
            "publication_name": "Tech Newsletter",
            "domain": "tech.substack.com",
            "membership_state": "subscribed",
        },
        {
            "publication_id": "456",
            "publication_name": "Science Weekly",
            "domain": "science-weekly.com",
            "membership_state": "paid_subscriber",
        },
    ]
    assert subscriptions == expected
    mock_fetch.assert_awaited_once()
