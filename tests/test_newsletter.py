import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from curl_cffi import requests as curl_requests

from substack_api import Newsletter, User
from substack_api._http import DEFAULT_TIMEOUT
from substack_api.newsletter import (
    DISCOVERY_HEADERS,
    HEADERS,
    SEARCH_URL,
    _host_from_url,
    _match_publication,
)


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def newsletter_url():
    return "https://testblog.substack.com"


@pytest.fixture
def mock_post_items():
    return [
        {
            "id": 101,
            "title": "First Test Post",
            "canonical_url": "https://testblog.substack.com/p/first-test-post",
        },
        {
            "id": 102,
            "title": "Second Test Post",
            "canonical_url": "https://testblog.substack.com/p/second-test-post",
        },
        {
            "id": 103,
            "title": "Third Test Post",
            "canonical_url": "https://testblog.substack.com/p/third-test-post",
        },
    ]


@pytest.fixture
def mock_recommendations():
    return [
        {"recommendedPublication": {"subdomain": "newsletter1", "custom_domain": None}},
        {"recommendedPublication": {"subdomain": "newsletter2", "custom_domain": None}},
        {
            "recommendedPublication": {
                "subdomain": "newsletter3",
                "custom_domain": "https://custom.domain.com",
            }
        },
    ]


@pytest.fixture
def mock_authors():
    return [
        {"handle": "author1", "name": "Author One"},
        {"handle": "author2", "name": "Author Two"},
    ]


def make_http_status_error(status_code: int) -> curl_requests.exceptions.HTTPError:
    response = curl_requests.Response(None)
    response.status_code = status_code
    return curl_requests.exceptions.HTTPError(f"{status_code} error", response=response)


def test_newsletter_init(newsletter_url):
    newsletter = Newsletter(newsletter_url)
    assert newsletter.url == newsletter_url


def test_newsletter_init_strips_trailing_slash(newsletter_url):
    newsletter = Newsletter(f"{newsletter_url}/")
    assert newsletter.url == newsletter_url


def test_newsletter_string_representation(newsletter_url):
    newsletter = Newsletter(newsletter_url)
    assert str(newsletter) == f"Newsletter: {newsletter_url}"
    assert repr(newsletter) == f"Newsletter(url={newsletter_url})"


@patch("substack_api.newsletter.async_get", new_callable=AsyncMock)
def test_fetch_paginated_posts_single_page(mock_get, newsletter_url, mock_post_items):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_post_items
    mock_get.return_value = mock_response

    newsletter = Newsletter(newsletter_url)
    params = {"sort": "new"}
    results = run(newsletter._fetch_paginated_posts(params, limit=None))

    mock_get.assert_awaited_once_with(
        f"{newsletter_url}/api/v1/archive?sort=new&offset=0&limit=15",
        headers=HEADERS,
        timeout=DEFAULT_TIMEOUT,
    )
    assert len(results) == 3
    assert isinstance(results[0], dict)
    assert results[0]["canonical_url"] == mock_post_items[0]["canonical_url"]


@patch("substack_api.newsletter.async_get", new_callable=AsyncMock)
def test_fetch_paginated_posts_single_page_with_proxy(
    mock_get, newsletter_url, mock_post_items
):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_post_items
    mock_get.return_value = mock_response

    newsletter = Newsletter(newsletter_url, proxy="http://127.0.0.1:8080")
    params = {"sort": "new"}
    run(newsletter._fetch_paginated_posts(params, limit=None))

    mock_get.assert_awaited_once_with(
        f"{newsletter_url}/api/v1/archive?sort=new&offset=0&limit=15",
        headers=HEADERS,
        proxy="http://127.0.0.1:8080",
        timeout=DEFAULT_TIMEOUT,
    )


@patch("substack_api.newsletter.async_get", new_callable=AsyncMock)
def test_fetch_paginated_posts_multiple_pages(mock_get, newsletter_url, mock_post_items):
    mock_response_1 = MagicMock()
    mock_response_1.status_code = 200
    mock_response_1.json.return_value = mock_post_items

    mock_response_2 = MagicMock()
    mock_response_2.status_code = 200
    mock_response_2.json.return_value = [
        {
            "id": 104,
            "title": "Fourth Test Post",
            "canonical_url": "https://testblog.substack.com/p/fourth-test-post",
        }
    ]

    mock_get.side_effect = [mock_response_1, mock_response_2]

    newsletter = Newsletter(newsletter_url)
    params = {"sort": "new"}
    results = run(newsletter._fetch_paginated_posts(params, page_size=3))

    assert mock_get.await_count == 2
    assert len(results) == 4


@patch("substack_api.newsletter.async_get", new_callable=AsyncMock)
def test_fetch_paginated_posts_with_limit(mock_get, newsletter_url, mock_post_items):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_post_items
    mock_get.return_value = mock_response

    newsletter = Newsletter(newsletter_url)
    params = {"sort": "new"}
    results = run(newsletter._fetch_paginated_posts(params, limit=2))

    assert len(results) == 2
    assert results[0]["canonical_url"] == mock_post_items[0]["canonical_url"]


@patch("substack_api.newsletter.async_get", new_callable=AsyncMock)
def test_fetch_paginated_posts_error_response(mock_get, newsletter_url):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = make_http_status_error(404)
    mock_get.return_value = mock_response

    newsletter = Newsletter(newsletter_url)
    params = {"sort": "new"}

    with pytest.raises(curl_requests.exceptions.HTTPError):
        run(newsletter._fetch_paginated_posts(params))


@patch("substack_api.newsletter.async_get", new_callable=AsyncMock)
def test_fetch_paginated_posts_empty_first_response(mock_get, newsletter_url):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    mock_get.return_value = mock_response

    newsletter = Newsletter(newsletter_url)
    params = {"sort": "new"}
    results = run(newsletter._fetch_paginated_posts(params))

    assert results == []
    assert mock_get.await_count == 1


@patch("substack_api.newsletter.Newsletter._fetch_paginated_posts", new_callable=AsyncMock)
def test_get_posts(mock_fetch, newsletter_url):
    newsletter = Newsletter(newsletter_url)

    run(newsletter.get_posts())
    mock_fetch.assert_awaited_once_with({"sort": "new"}, None)

    mock_fetch.reset_mock()
    run(newsletter.get_posts(sorting="top", limit=10))
    mock_fetch.assert_awaited_once_with({"sort": "top"}, 10)


@patch("substack_api.newsletter.Newsletter._fetch_paginated_posts", new_callable=AsyncMock)
def test_search_posts(mock_fetch, newsletter_url):
    newsletter = Newsletter(newsletter_url)

    run(newsletter.search_posts("test query"))
    mock_fetch.assert_awaited_once_with({"sort": "new", "search": "test query"}, None)

    mock_fetch.reset_mock()
    run(newsletter.search_posts("test query", limit=5))
    mock_fetch.assert_awaited_once_with({"sort": "new", "search": "test query"}, 5)


@patch("substack_api.newsletter.Newsletter._fetch_paginated_posts", new_callable=AsyncMock)
def test_get_podcasts(mock_fetch, newsletter_url):
    newsletter = Newsletter(newsletter_url)

    run(newsletter.get_podcasts())
    mock_fetch.assert_awaited_once_with({"sort": "new", "type": "podcast"}, None)

    mock_fetch.reset_mock()
    run(newsletter.get_podcasts(limit=3))
    mock_fetch.assert_awaited_once_with({"sort": "new", "type": "podcast"}, 3)


@patch(
    "substack_api.newsletter.Newsletter._make_request",
    new_callable=AsyncMock,
)
@patch(
    "substack_api.newsletter.Newsletter._resolve_publication_id",
    new_callable=AsyncMock,
)
def test_get_recommendations_success_via_resolve(
    mock_resolve, mock_make_request, newsletter_url, mock_recommendations
):
    mock_resolve.return_value = 123

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_recommendations
    mock_make_request.return_value = mock_resp

    newsletter = Newsletter(newsletter_url)
    recommendations = run(newsletter.get_recommendations())

    mock_resolve.assert_awaited_once()
    mock_make_request.assert_awaited_once_with(
        f"{newsletter_url}/api/v1/recommendations/from/123",
        timeout=DEFAULT_TIMEOUT,
    )
    assert len(recommendations) == 3
    assert all(isinstance(rec, Newsletter) for rec in recommendations)
    assert recommendations[0].url == "newsletter1.substack.com"
    assert recommendations[2].url == "https://custom.domain.com"


@patch(
    "substack_api.newsletter.Newsletter._make_request",
    new_callable=AsyncMock,
)
@patch("substack_api.newsletter.Newsletter.get_posts", new_callable=AsyncMock)
@patch(
    "substack_api.newsletter.Newsletter._resolve_publication_id",
    new_callable=AsyncMock,
)
def test_get_recommendations_fallback_to_posts(
    mock_resolve, mock_get_posts, mock_make_request, newsletter_url, mock_recommendations
):
    mock_resolve.return_value = None

    post_mock = MagicMock()
    post_mock.get_metadata = AsyncMock(return_value={"publication_id": 456})
    mock_get_posts.return_value = [post_mock]

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_recommendations
    mock_make_request.return_value = mock_resp

    newsletter = Newsletter(newsletter_url)
    recommendations = run(newsletter.get_recommendations())

    mock_resolve.assert_awaited_once()
    mock_get_posts.assert_awaited_once_with(limit=1)
    mock_make_request.assert_awaited_once_with(
        f"{newsletter_url}/api/v1/recommendations/from/456",
        timeout=DEFAULT_TIMEOUT,
    )
    assert len(recommendations) == 3


@patch("substack_api.newsletter.Newsletter.get_posts", new_callable=AsyncMock)
@patch(
    "substack_api.newsletter.Newsletter._resolve_publication_id",
    new_callable=AsyncMock,
)
def test_get_recommendations_no_publication_id(
    mock_resolve, mock_get_posts, newsletter_url
):
    mock_resolve.return_value = None
    mock_get_posts.return_value = []

    newsletter = Newsletter(newsletter_url)
    recommendations = run(newsletter.get_recommendations())

    assert recommendations == []


@patch("substack_api.newsletter.Newsletter.get_posts", new_callable=AsyncMock)
@patch(
    "substack_api.newsletter.Newsletter._resolve_publication_id",
    new_callable=AsyncMock,
)
def test_get_recommendations_fallback_exception(
    mock_resolve, mock_get_posts, newsletter_url
):
    mock_resolve.return_value = None
    mock_get_posts.side_effect = Exception("Error fetching posts")

    newsletter = Newsletter(newsletter_url)
    recommendations = run(newsletter.get_recommendations())

    assert recommendations == []


@patch(
    "substack_api.newsletter.Newsletter._make_request",
    new_callable=AsyncMock,
)
@patch(
    "substack_api.newsletter.Newsletter._resolve_publication_id",
    new_callable=AsyncMock,
)
def test_get_recommendations_api_error(mock_resolve, mock_make_request, newsletter_url):
    mock_resolve.return_value = 123

    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.raise_for_status.side_effect = make_http_status_error(404)
    mock_make_request.return_value = mock_resp

    newsletter = Newsletter(newsletter_url)

    with pytest.raises(curl_requests.exceptions.HTTPError):
        run(newsletter.get_recommendations())


@patch(
    "substack_api.newsletter.Newsletter._make_request",
    new_callable=AsyncMock,
)
@patch(
    "substack_api.newsletter.Newsletter._resolve_publication_id",
    new_callable=AsyncMock,
)
def test_get_recommendations_empty_response(
    mock_resolve, mock_make_request, newsletter_url
):
    mock_resolve.return_value = 123

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = []
    mock_make_request.return_value = mock_resp

    newsletter = Newsletter(newsletter_url)
    recommendations = run(newsletter.get_recommendations())

    assert recommendations == []


@patch(
    "substack_api.newsletter.Newsletter._make_request",
    new_callable=AsyncMock,
)
@patch(
    "substack_api.newsletter.Newsletter._resolve_publication_id",
    new_callable=AsyncMock,
)
def test_get_recommendations_null_response(
    mock_resolve, mock_make_request, newsletter_url
):
    mock_resolve.return_value = 123

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = None
    mock_make_request.return_value = mock_resp

    newsletter = Newsletter(newsletter_url)
    recommendations = run(newsletter.get_recommendations())

    assert recommendations == []


@patch("substack_api.newsletter.Newsletter._make_request", new_callable=AsyncMock)
def test_get_authors(mock_make_request, newsletter_url, mock_authors):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_authors
    mock_make_request.return_value = mock_response

    newsletter = Newsletter(newsletter_url)
    authors = run(newsletter.get_authors())

    expected_url = f"{newsletter_url}/api/v1/publication/users/ranked?public=true"
    mock_make_request.assert_awaited_once_with(expected_url, timeout=DEFAULT_TIMEOUT)
    assert len(authors) == 2
    assert all(isinstance(author, User) for author in authors)
    assert authors[0].username == "author1"
    assert authors[1].username == "author2"


@patch("substack_api.newsletter.Newsletter._make_request", new_callable=AsyncMock)
def test_get_authors_empty_response(mock_make_request, newsletter_url):
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_make_request.return_value = mock_response

    newsletter = Newsletter(newsletter_url)
    authors = run(newsletter.get_authors())

    assert authors == []


@patch("substack_api.newsletter.async_get", new_callable=AsyncMock)
def test_resolve_publication_id(mock_get, newsletter_url):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "publications": [
            {
                "id": 123,
                "subdomain": "testblog",
                "custom_domain": None,
            }
        ]
    }
    mock_get.return_value = mock_response

    newsletter = Newsletter(newsletter_url)
    publication_id = run(newsletter._resolve_publication_id())

    assert publication_id == 123
    mock_get.assert_awaited_once_with(
        SEARCH_URL,
        headers=DISCOVERY_HEADERS,
        params={
            "query": "testblog.substack.com",
            "page": 0,
            "limit": 25,
            "skipExplanation": "true",
            "sort": "relevance",
        },
        timeout=DEFAULT_TIMEOUT,
    )


def test_host_from_url():
    assert _host_from_url("https://testblog.substack.com") == "testblog.substack.com"
    assert _host_from_url("testblog.substack.com") == "testblog.substack.com"
    assert _host_from_url("https://custom.example.com") == "custom.example.com"
    assert (
        _host_from_url("https://testblog.substack.com:8080")
        == "testblog.substack.com:8080"
    )
    assert _host_from_url("https://TestBlog.Substack.COM") == "testblog.substack.com"


def test_match_publication():
    search_results = {
        "publications": [
            {
                "id": 123,
                "subdomain": "testblog",
                "custom_domain": None,
            },
            {
                "id": 456,
                "subdomain": "otherblog",
                "custom_domain": "https://custom.example.com",
            },
            {
                "id": 789,
                "subdomain": "thirdblog",
                "custom_domain": "custom2.example.com",
            },
        ]
    }

    match = _match_publication(search_results, "testblog.substack.com")
    assert match is not None
    assert match["id"] == 123

    match = _match_publication(search_results, "custom.example.com")
    assert match is not None
    assert match["id"] == 456

    match = _match_publication(search_results, "custom2.example.com")
    assert match is not None
    assert match["id"] == 789

    match = _match_publication(search_results, "nonexistent.substack.com")
    assert match is None

    search_results_mixed_case = {
        "publications": [
            {
                "id": 999,
                "subdomain": "TestBlog",
                "custom_domain": None,
            }
        ]
    }
    match = _match_publication(search_results_mixed_case, "testblog.substack.com")
    assert match is not None
    assert match["id"] == 999
