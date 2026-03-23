# Newsletter

The `Newsletter` class provides access to Substack publications.

## Class Definition

```python
Newsletter(url: str, auth: Optional[SubstackAuth] = None)
```

### Parameters

- `url` (str): The URL of the Substack newsletter
- `auth` (Optional[SubstackAuth]): Authentication handler for accessing paywalled content

## Methods

### `await _fetch_paginated_posts(params: Dict[str, str], limit: Optional[int] = None, page_size: int = 15) -> List[Dict[str, Any]]`

Helper method to fetch paginated posts with different query parameters.

#### Parameters

- `params` (Dict[str, str]): Dictionary of query parameters to include in the API request
- `limit` (Optional[int]): Maximum number of posts to return
- `page_size` (int): Number of posts to retrieve per page request

#### Returns

- `List[Dict[str, Any]]`: List of post data dictionaries

### `await get_posts(sorting: str = "new", limit: Optional[int] = None) -> List[Post]`

Get posts from the newsletter with specified sorting.

#### Parameters

- `sorting` (str): Sorting order for the posts ("new", "top", "pinned", or "community")
- `limit` (Optional[int]): Maximum number of posts to return

#### Returns

- `List[Post]`: List of Post objects

### `await search_posts(query: str, limit: Optional[int] = None) -> List[Post]`

Search posts in the newsletter with the given query.

#### Parameters

- `query` (str): Search query string
- `limit` (Optional[int]): Maximum number of posts to return

#### Returns

- `List[Post]`: List of Post objects matching the search query

### `await get_podcasts(limit: Optional[int] = None) -> List[Post]`

Get podcast posts from the newsletter.

#### Parameters

- `limit` (Optional[int]): Maximum number of podcast posts to return

#### Returns

- `List[Post]`: List of Post objects representing podcast posts

### `await get_recommendations() -> List[Newsletter]`

Get recommended publications for this newsletter.

#### Returns

- `List[Newsletter]`: List of recommended Newsletter objects

### `await get_authors() -> List[User]`

Get authors of the newsletter.

#### Returns

- `List[User]`: List of User objects representing the authors

## Example Usage

```python
import asyncio

from substack_api import Newsletter, SubstackAuth


async def main():
    newsletter = Newsletter("https://example.substack.com")

    recent_posts = await newsletter.get_posts(limit=5)
    for post in recent_posts:
        metadata = await post.get_metadata()
        print(f"Post: {metadata['title']}")

    search_results = await newsletter.search_posts("machine learning", limit=3)
    for post in search_results:
        metadata = await post.get_metadata()
        print(f"Found: {metadata['title']}")

    podcasts = await newsletter.get_podcasts(limit=2)
    for podcast in podcasts:
        metadata = await podcast.get_metadata()
        print(f"Podcast: {metadata['title']}")

    authors = await newsletter.get_authors()
    for author in authors:
        await author.get_raw_data()
        print(f"Author: {author.name}")

    recommendations = await newsletter.get_recommendations()
    for rec in recommendations:
        print(f"Recommended: {rec.url}")

    auth = SubstackAuth(cookies_path="cookies.json")
    try:
        authenticated_newsletter = Newsletter("https://example.substack.com", auth=auth)
        paywalled_posts = await authenticated_newsletter.get_posts(limit=5)
        for post in paywalled_posts:
            if await post.is_paywalled():
                content = await post.get_content()
                print(f"Paywalled content: {content[:100]}...")
    finally:
        await auth.aclose()


asyncio.run(main())
```
