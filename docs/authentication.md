# Authentication

The Substack API library supports authentication to access paywalled content. This feature allows users to access their own subscribed content programmatically by providing their session cookies from a logged-in Substack session.

## Overview

Authentication in the Substack API library works by:

1. Loading session cookies from a JSON file
2. Using those cookies to make authenticated async HTTP requests
3. Automatically handling authentication for both `Newsletter` and `Post` objects

## Setting Up Authentication

### 1. Export Your Cookies

To use authentication, you need to export your browser cookies from a logged-in Substack session. The cookies should be saved in JSON format with this structure:

```json
[
  {
    "name": "substack.sid",
    "value": "your_session_id_here",
    "domain": ".substack.com",
    "path": "/",
    "secure": true
  },
  {
    "name": "substack.lli",
    "value": "your_lli_value_here",
    "domain": ".substack.com",
    "path": "/",
    "secure": true
  },
  ...
]
```

### 2. Create Authentication Object

```python
import asyncio

from substack_api import SubstackAuth


async def main():
    auth = SubstackAuth(cookies_path="path/to/your/cookies.json")
    try:
        if auth.authenticated:
            print("Authentication successful!")
        else:
            print("Authentication failed - check your cookies file")
    finally:
        await auth.aclose()


asyncio.run(main())
```

## Using Authentication

### With Newsletter Objects

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

### With Post Objects

```python
import asyncio

from substack_api import Post, SubstackAuth


async def main():
    auth = SubstackAuth(cookies_path="cookies.json")
    try:
        post = Post("https://example.substack.com/p/paywalled-post", auth=auth)

        if await post.is_paywalled():
            print("This post is paywalled")

        content = await post.get_content()
    finally:
        await auth.aclose()


asyncio.run(main())
```

### Checking Paywall Status

```python
import asyncio

from substack_api import Post


async def main():
    post = Post("https://example.substack.com/p/some-post")

    if await post.is_paywalled():
        print("This post requires authentication to access full content")

        from substack_api import SubstackAuth

        auth = SubstackAuth(cookies_path="cookies.json")
        try:
            authenticated_post = Post(post.url, auth=auth)
            content = await authenticated_post.get_content()
        finally:
            await auth.aclose()
    else:
        content = await post.get_content()


asyncio.run(main())
```

## How to Get Your Cookies

### Method 1: Browser Developer Tools

1. Log in to Substack in your browser
2. Open Developer Tools (F12 or right-click → Inspect)
3. Go to the Application/Storage tab
4. Find "Cookies" → "https://substack.com"
5. Export their values to a JSON file in the required format

### Method 2: Browser Extensions

You can use browser extensions that export cookies to JSON format. Make sure to:
- Only export cookies for the `.substack.com` domain
- Save in the JSON format shown above

## Security Considerations

**Important Security Notes:**

- **Only use your own cookies** from your own authenticated session
- **Keep your cookies file secure** - treat it like a password
- **Don't share your cookies** with others or commit them to version control
- **Cookies may expire** - you may need to refresh them periodically
- **Respect Substack's Terms of Service** when using authentication features

## Error Handling

```python
import asyncio

from substack_api import SubstackAuth, Post


async def main():
    auth = None
    try:
        auth = SubstackAuth(cookies_path="cookies.json")

        if not auth.authenticated:
            print("Warning: Authentication failed, using public access only")
            auth = None

        post = Post("https://example.substack.com/p/some-post", auth=auth)
        content = await post.get_content()

        if content is None and await post.is_paywalled():
            print("This content is paywalled and requires authentication")
    finally:
        if auth is not None:
            await auth.aclose()


asyncio.run(main())
```

## API Reference

See the [SubstackAuth API documentation](api-reference/auth.md) for detailed information about the authentication class and its methods.
