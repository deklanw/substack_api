# Substack API

An unofficial Python library for interacting with Substack.

## Overview

The Substack API library provides a simple interface to interact with Substack newsletters, users, posts, and categories. This unofficial API wrapper allows you to:

- Browse newsletter content
- Retrieve user profiles and subscriptions
- Access post content and metadata
- Discover newsletters by category
- Access paywalled content **that you have access to** with user-provided authentication

## Quick Start

```python
import asyncio

from substack_api import Newsletter, User, Post, Category, SubstackAuth


async def main():
    newsletter = Newsletter("https://example.substack.com")
    posts = await newsletter.get_posts(limit=5)

    user = User("username")
    subscriptions = await user.get_subscriptions()

    post = Post("https://example.substack.com/p/post-slug")
    content = await post.get_content()

    tech_category = await Category.create(name="Technology")
    tech_newsletters = await tech_category.get_newsletters()

    auth = SubstackAuth(cookies_path="cookies.json")
    try:
        authenticated_post = Post(
            "https://example.substack.com/p/paywalled-post", auth=auth
        )
        paywalled_content = await authenticated_post.get_content()
    finally:
        await auth.aclose()


asyncio.run(main())
```

## Features

- Simple, intuitive Python API
- Command-line interface for quick terminal access
- Comprehensive access to Substack data
- Pagination support for large collections
- Automatic caching to minimize API calls
- Authentication support for accessing paywalled content

## Important Note

This is an **unofficial** API wrapper. It is not affiliated with or endorsed by Substack. Be mindful of Substack's terms of service when using this library.
