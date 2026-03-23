# User Guide

## Basic Concepts

The Substack API library is organized around five main classes:

- `User` - Represents a Substack user profile
- `Newsletter` - Represents a Substack publication
- `Post` - Represents an individual post on Substack
- `Category` - Represents a Substack category of newsletters
- `SubstackAuth` - Handles authentication for accessing paywalled content

Each class provides methods to access different aspects of the Substack ecosystem.
All network-bound methods are asynchronous and should be awaited.

## Working with Newsletters

The `Newsletter` class is the main entry point for interacting with Substack publications:

```python
import asyncio

from substack_api import Newsletter


async def main():
    newsletter = Newsletter("https://example.substack.com")

    recent_posts = await newsletter.get_posts(limit=10)
    search_results = await newsletter.search_posts("artificial intelligence")
    podcasts = await newsletter.get_podcasts()
    authors = await newsletter.get_authors()
    recommendations = await newsletter.get_recommendations()


asyncio.run(main())
```

### Accessing Paywalled Newsletter Content

To access paywalled posts from a newsletter, provide authentication:

```python
import asyncio

from substack_api import Newsletter, SubstackAuth


async def main():
    auth = SubstackAuth(cookies_path="cookies.json")
    try:
        newsletter = Newsletter("https://example.substack.com", auth=auth)
        posts = await newsletter.get_posts(limit=10)

        for post in posts:
            if await post.is_paywalled():
                content = await post.get_content()
                print(f"Paywalled content: {content[:100]}...")
    finally:
        await auth.aclose()


asyncio.run(main())
```

## Working with Users

The `User` class allows you to access information about Substack users:

```python
import asyncio

from substack_api import User


async def main():
    user = User("username")
    user_no_redirect = User("username", follow_redirects=False)

    user_data = await user.get_raw_data()
    user_id = user.id
    name = user.name
    subscriptions = await user.get_subscriptions()

    if user.was_redirected:
        print(f"Original handle '{user.original_username}' was redirected to '{user.username}'")


asyncio.run(main())
```

### Handle Redirects

Substack users sometimes change handles. The `User` class automatically handles these redirects by default:

```python
# This will work even if "old_username" has been renamed to "new_username"
user = User("old_username")  # follow_redirects=True by default

# Check if a redirect happened
if user.was_redirected:
    print(f"User was redirected from {user.original_username} to {user.username}")
```

## Working with Posts

The `Post` class allows you to access information about individual Substack posts:

```python
import asyncio

from substack_api import Post


async def main():
    post = Post("https://example.substack.com/p/post-slug")

    content = await post.get_content()
    metadata = await post.get_metadata()

    if await post.is_paywalled():
        print("This post requires a subscription")


asyncio.run(main())
```

### Accessing Paywalled Content

To access paywalled content, you need to provide authentication:

```python
import asyncio

from substack_api import Post, SubstackAuth


async def main():
    auth = SubstackAuth(cookies_path="cookies.json")
    try:
        post = Post("https://example.substack.com/p/paywalled-post", auth=auth)
        content = await post.get_content()
    finally:
        await auth.aclose()


asyncio.run(main())
```

## Working with Categories

The `Category` class allows you to discover newsletters by category:

```python
import asyncio

from substack_api import Category

from substack_api.category import list_all_categories


async def main():
    categories = await list_all_categories()

    category = await Category.create(name="Technology")
    category_by_id = await Category.create(id=12)

    newsletters = await category.get_newsletters()
    newsletter_metadata = await category.get_newsletter_metadata()


asyncio.run(main())
```

## Authentication

The library supports authentication to access paywalled content. See the [Authentication Guide](authentication.md) for detailed information on setting up and using authentication.

```python
import asyncio

from substack_api import Newsletter, Post, SubstackAuth


async def main():
    auth = SubstackAuth(cookies_path="cookies.json")
    try:
        newsletter = Newsletter("https://example.substack.com", auth=auth)
        post = Post("https://example.substack.com/p/paywalled-post", auth=auth)
    finally:
        await auth.aclose()


asyncio.run(main())
```

## Caching Behavior

By default, the library caches API responses to minimize the number of requests. You can force a refresh of the data by passing `force_refresh=True` to relevant methods:

```python
import asyncio

# Force refresh of post data
asyncio.run(post.get_metadata(force_refresh=True))

# Force refresh of user data
asyncio.run(user.get_raw_data(force_refresh=True))
```
