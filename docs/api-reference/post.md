# Post

The `Post` class provides access to individual Substack posts.

## Class Definition

```python
Post(url: str, auth: Optional[SubstackAuth] = None)
```

### Parameters

- `url` (str): The URL of the Substack post
- `auth` (Optional[SubstackAuth]): Authentication handler for accessing paywalled content

## Methods

### `await _fetch_post_data(force_refresh: bool = False) -> Dict[str, Any]`

Fetch the raw post data from the API and cache it.

#### Parameters

- `force_refresh` (bool): Whether to force a refresh of the data, ignoring the cache

#### Returns

- `Dict[str, Any]`: Full post metadata

### `await get_metadata(force_refresh: bool = False) -> Dict[str, Any]`

Get metadata for the post.

#### Parameters

- `force_refresh` (bool): Whether to force a refresh of the data, ignoring the cache

#### Returns

- `Dict[str, Any]`: Full post metadata

### `await get_content(force_refresh: bool = False) -> Optional[str]`

Get the HTML content of the post.

#### Parameters

- `force_refresh` (bool): Whether to force a refresh of the data, ignoring the cache

#### Returns

- `Optional[str]`: HTML content of the post, or None if not available (e.g., for paywalled content without authentication)

### `await is_paywalled() -> bool`

Check if the post is paywalled.

#### Returns

- `bool`: True if the post requires a subscription to access full content

## Example Usage

```python
import asyncio

from substack_api import Post, SubstackAuth


async def main():
    post = Post("https://example.substack.com/p/post-slug")

    metadata = await post.get_metadata()
    print(f"Title: {metadata['title']}")

    if await post.is_paywalled():
        print("This post is paywalled")

        auth = SubstackAuth(cookies_path="cookies.json")
        try:
            authenticated_post = Post(
                "https://example.substack.com/p/post-slug", auth=auth
            )
            content = await authenticated_post.get_content()
        finally:
            await auth.aclose()
    else:
        content = await post.get_content()

    print(f"Content length: {len(content) if content else 0}")


asyncio.run(main())
```
