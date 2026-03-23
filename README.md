# Substack API

An unofficial Python client library for interacting with Substack newsletters and content.

## Overview

This library provides Python interfaces for interacting with Substack's unofficial API, allowing you to:

- Retrieve newsletter posts, podcasts, and recommendations
- Get user profile information and subscriptions
- Fetch post content and metadata
- Search for posts within newsletters
- Access paywalled content **that you have written or paid for** with user-provided authentication

## Installation

```bash
# Using pip
pip install substack-api

# Using uv
uv add substack-api
```

## Command-Line Interface

The library includes a CLI for quick access from the terminal. All commands output JSON by default.

```bash
# Get the 5 newest posts from a newsletter
substack newsletter posts https://example.substack.com --limit 5

# Search for posts
substack newsletter search https://example.substack.com "machine learning"

# Get metadata for a specific post
substack post metadata https://example.substack.com/p/my-post --pretty

# Look up a user's subscriptions
substack user subscriptions username

# Browse categories
substack categories
substack category newsletters --name Technology

# Run the quickstart guide for a full command reference
substack quickstart
```

Use `--pretty` for human-readable output and `--cookies <path>` for authenticated access to paywalled content.

## Python Usage Examples

All network-backed library APIs are asynchronous and should be awaited.

### Working with Newsletters

```python
import asyncio

from substack_api import Newsletter


async def main():
    newsletter = Newsletter("https://example.substack.com")

    recent_posts = await newsletter.get_posts(limit=5)
    top_posts = await newsletter.get_posts(sorting="top", limit=10)
    search_results = await newsletter.search_posts("machine learning", limit=3)
    podcasts = await newsletter.get_podcasts(limit=5)
    recommendations = await newsletter.get_recommendations()
    authors = await newsletter.get_authors()


asyncio.run(main())
```

### Working with Posts

```python
import asyncio

from substack_api import Post


async def main():
    post = Post("https://example.substack.com/p/post-slug")

    metadata = await post.get_metadata()
    content = await post.get_content()


asyncio.run(main())
```

### Accessing Paywalled Content with Authentication

To access paywalled content, you need to provide your own session cookies from a logged-in Substack session:

```python
import asyncio

from substack_api import Newsletter, Post, SubstackAuth


async def main():
    auth = SubstackAuth(cookies_path="path/to/your/cookies.json")
    try:
        newsletter = Newsletter("https://example.substack.com", auth=auth)
        posts = await newsletter.get_posts(limit=5)

        post = Post("https://example.substack.com/p/paywalled-post", auth=auth)
        content = await post.get_content()

        if await post.is_paywalled():
            print("This post requires a subscription")
    finally:
        await auth.aclose()


asyncio.run(main())
```

#### Getting Your Cookies

To access paywalled content, you need to export your browser cookies from a logged-in Substack session. The cookies should be in JSON format with the following structure:

```json
[
  {
    "name": "substack.sid",
    "value": "your_session_id",
    "domain": ".substack.com",
    "path": "/",
    "secure": true
  },
  {
    "name": "substack.lli", 
    "value": "your_lli_value",
    "domain": ".substack.com",
    "path": "/",
    "secure": true
  },
  ...
]
```

**Important**: Only use your own cookies from your own authenticated session. **This feature is intended for users to access their own subscribed or authored content programmatically.**

### Working with Users

```python
import asyncio

from substack_api import User


async def main():
    user = User("username")

    profile_data = await user.get_raw_data()
    user_id = user.id
    name = user.name
    subscriptions = await user.get_subscriptions()


asyncio.run(main())
```

#### Handling Renamed Accounts
Substack allows users to change their handle (username) at any time. When this happens, the old API endpoints return 404 errors. This library automatically handles these redirects by default.
##### Automatic Redirect Handling

```python
import asyncio

from substack_api import User


async def main():
    user = User("oldhandle")
    await user.get_raw_data()

    if user.was_redirected:
        print(f"User was renamed from {user.original_username} to {user.username}")


asyncio.run(main())
```

##### Disable Redirect Following

If you prefer to handle 404s yourself:

```python
# Disable automatic redirect following
user = User("oldhandle", follow_redirects=False)
```

##### Manual Handle Resolution

You can also manually resolve handle redirects:

```python
import asyncio

from substack_api import resolve_handle_redirect


async def main():
    new_handle = await resolve_handle_redirect("oldhandle")
    if new_handle:
        print(f"Handle was renamed to: {new_handle}")


asyncio.run(main())
```
## Limitations

- This is an unofficial library and not endorsed by Substack
- APIs may change without notice, potentially breaking functionality
- Rate limiting may be enforced by Substack
- **Authentication requires users to provide their own session cookies**
- **Users are responsible for complying with Substack's terms of service when using authentication features**

## Development

### Running Tests

```bash
# Install dev dependencies
uv sync --group dev

# Run tests
uv run --group dev pytest
```

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This package is not affiliated with, endorsed by, or connected to Substack in any way. It is an independent project created to make Substack content more accessible through Python.
