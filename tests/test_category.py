import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from substack_api._http import DEFAULT_TIMEOUT
from substack_api.category import Category, HEADERS, list_all_categories
from substack_api.newsletter import Newsletter


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def mock_categories():
    return [
        {"name": "Technology", "id": 1},
        {"name": "Finance", "id": 2},
        {"name": "Culture", "id": 3},
    ]


@pytest.fixture
def mock_newsletters_data():
    return [
        {
            "id": 101,
            "name": "Tech Insights",
            "paid_subscriber_count": 1500,
            "base_url": "https://techinsights.substack.com",
        },
        {
            "id": 102,
            "name": "Future Tech",
            "paid_subscriber_count": 2500,
            "base_url": "https://futuretech.substack.com",
        },
        {
            "id": 103,
            "name": "AI Weekly",
            "paid_subscriber_count": 3000,
            "base_url": "https://aiweekly.substack.com",
        },
    ]


@patch("substack_api.category.async_get", new_callable=AsyncMock)
def test_list_all_categories(mock_get, mock_categories):
    mock_response = MagicMock()
    mock_response.json.return_value = mock_categories
    mock_get.return_value = mock_response

    categories = run(list_all_categories())

    assert len(categories) == 3
    assert categories[0] == ("Technology", 1)
    assert categories[1] == ("Finance", 2)
    assert categories[2] == ("Culture", 3)
    mock_get.assert_awaited_once_with(
        "https://substack.com/api/v1/categories",
        headers=HEADERS,
        timeout=DEFAULT_TIMEOUT,
    )


@patch("substack_api.category.async_get", new_callable=AsyncMock)
def test_list_all_categories_with_proxy(mock_get, mock_categories):
    mock_response = MagicMock()
    mock_response.json.return_value = mock_categories
    mock_get.return_value = mock_response

    run(list_all_categories(proxy="http://127.0.0.1:8080"))

    mock_get.assert_awaited_once_with(
        "https://substack.com/api/v1/categories",
        headers=HEADERS,
        proxy="http://127.0.0.1:8080",
        timeout=DEFAULT_TIMEOUT,
    )


@patch("substack_api.category.list_all_categories", new_callable=AsyncMock)
def test_category_init(mock_list_all_categories):
    category = Category(name="Technology", id=1)
    assert category.name == "Technology"
    assert category.id == 1
    mock_list_all_categories.assert_not_awaited()

    mock_list_all_categories.reset_mock()
    mock_list_all_categories.return_value = [
        ("Technology", 1),
        ("Finance", 2),
        ("Culture", 3),
    ]

    category = run(Category.create(name="Finance"))
    assert category.name == "Finance"
    assert category.id == 2
    mock_list_all_categories.assert_awaited_once()

    mock_list_all_categories.reset_mock()

    category = run(Category.create(id=3))
    assert category.name == "Culture"
    assert category.id == 3
    mock_list_all_categories.assert_awaited_once()


@patch("substack_api.category.list_all_categories", new_callable=AsyncMock)
def test_category_create_with_proxy(mock_list_all_categories):
    mock_list_all_categories.return_value = [
        ("Technology", 1),
        ("Finance", 2),
    ]

    category = run(Category.create(name="Finance", proxy="http://127.0.0.1:8080"))

    assert category.proxy == "http://127.0.0.1:8080"
    mock_list_all_categories.assert_awaited_once_with(proxy="http://127.0.0.1:8080")


def test_category_string_representation():
    category = Category(name="Technology", id=1)
    assert str(category) == "Technology (1)"
    assert repr(category) == "Category(name=Technology, id=1)"


@patch("substack_api.category.list_all_categories", new_callable=AsyncMock)
def test_get_id_from_name(mock_list_all_categories):
    categories_data = [
        ("Technology", 1),
        ("Finance", 2),
        ("Culture", 3),
    ]
    mock_list_all_categories.return_value = categories_data

    category = run(Category.create(name="Finance"))

    assert category.id == 2
    assert mock_list_all_categories.await_count == 1

    run(category._get_id_from_name())
    assert category.id == 2
    assert mock_list_all_categories.await_count == 2

    mock_list_all_categories.reset_mock()
    mock_list_all_categories.return_value = categories_data

    with pytest.raises(ValueError, match="Category name 'Invalid' not found"):
        run(Category.create(name="Invalid"))

    assert mock_list_all_categories.await_count == 1


@patch("substack_api.category.list_all_categories", new_callable=AsyncMock)
def test_get_name_from_id(mock_list_all_categories):
    categories_data = [
        ("Technology", 1),
        ("Finance", 2),
        ("Culture", 3),
    ]
    mock_list_all_categories.return_value = categories_data

    category = run(Category.create(id=3))

    assert category.name == "Culture"
    assert mock_list_all_categories.await_count == 1

    run(category._get_name_from_id())
    assert category.name == "Culture"
    assert mock_list_all_categories.await_count == 2

    mock_list_all_categories.reset_mock()
    mock_list_all_categories.return_value = categories_data

    with pytest.raises(ValueError, match="Category ID 999 not found"):
        run(Category.create(id=999))

    assert mock_list_all_categories.await_count == 1


@patch("substack_api.category.async_get", new_callable=AsyncMock)
def test_fetch_newsletters_data(mock_get, mock_newsletters_data):
    mock_response1 = MagicMock()
    mock_response1.json.return_value = {
        "publications": mock_newsletters_data[:2],
        "more": True,
    }

    mock_response2 = MagicMock()
    mock_response2.json.return_value = {
        "publications": mock_newsletters_data[2:],
        "more": False,
    }

    mock_get.side_effect = [mock_response1, mock_response2]

    category = Category(name="Technology", id=1)

    result = run(category._fetch_newsletters_data())
    assert len(result) == 3
    assert result == mock_newsletters_data[:2] + mock_newsletters_data[2:]
    assert mock_get.await_count == 2

    mock_get.reset_mock()
    result = run(category._fetch_newsletters_data())
    assert result == mock_newsletters_data
    mock_get.assert_not_awaited()

    mock_get.reset_mock()
    mock_get.side_effect = [mock_response1, mock_response2]
    run(category._fetch_newsletters_data(force_refresh=True))
    assert mock_get.await_count == 2


@patch("substack_api.category.Category._fetch_newsletters_data", new_callable=AsyncMock)
def test_get_newsletter_urls(mock_fetch_data, mock_newsletters_data):
    mock_fetch_data.return_value = mock_newsletters_data

    category = Category(name="Technology", id=1)
    urls = run(category.get_newsletter_urls())

    assert urls == [
        "https://techinsights.substack.com",
        "https://futuretech.substack.com",
        "https://aiweekly.substack.com",
    ]
    mock_fetch_data.assert_awaited_once()


@patch("substack_api.category.Category.get_newsletter_urls", new_callable=AsyncMock)
def test_get_newsletters(mock_get_urls):
    mock_urls = [
        "https://techinsights.substack.com",
        "https://futuretech.substack.com",
        "https://aiweekly.substack.com",
    ]
    mock_get_urls.return_value = mock_urls

    category = Category(name="Technology", id=1)
    newsletters = run(category.get_newsletters())

    assert len(newsletters) == 3
    assert all(isinstance(newsletter, Newsletter) for newsletter in newsletters)
    assert newsletters[0].url == "https://techinsights.substack.com"
    assert newsletters[1].url == "https://futuretech.substack.com"
    assert newsletters[2].url == "https://aiweekly.substack.com"
    mock_get_urls.assert_awaited_once()


@patch("substack_api.category.Category._fetch_newsletters_data", new_callable=AsyncMock)
def test_get_newsletter_metadata(mock_fetch_data, mock_newsletters_data):
    mock_fetch_data.return_value = mock_newsletters_data

    category = Category(name="Technology", id=1)
    metadata = run(category.get_newsletter_metadata())

    assert metadata == mock_newsletters_data
    mock_fetch_data.assert_awaited_once()


@patch("substack_api.category.Category._fetch_newsletters_data", new_callable=AsyncMock)
def test_refresh_data(mock_fetch_data):
    category = Category(name="Technology", id=1)
    run(category.refresh_data())

    mock_fetch_data.assert_awaited_with(force_refresh=True)
