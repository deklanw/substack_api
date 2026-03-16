# Command-Line Interface

The `substack` CLI provides terminal access to Substack newsletters, posts, users, and categories. All commands output JSON by default.

## Global Options

| Option | Description |
|--------|-------------|
| `--pretty` | Pretty-print JSON output with indentation |
| `--cookies PATH` | Path to a cookies JSON file for authenticated access to paywalled content |

## Newsletter Commands

### Get posts

```bash
substack newsletter posts <url> [--sort new|top|pinned|community] [--limit N]
```

Returns a list of post URLs from the newsletter.

```bash
# Get the 5 newest posts
substack newsletter posts https://example.substack.com --limit 5

# Get top posts
substack newsletter posts https://example.substack.com --sort top --limit 10
```

### Search posts

```bash
substack newsletter search <url> <query> [--limit N]
```

```bash
substack newsletter search https://example.substack.com "machine learning" --limit 3
```

### Get podcasts

```bash
substack newsletter podcasts <url> [--limit N]
```

### Get recommendations

```bash
substack newsletter recs <url>
```

Returns URLs of newsletters recommended by the given newsletter.

### Get authors

```bash
substack newsletter authors <url>
```

Returns usernames of the newsletter's authors.

## Post Commands

### Get metadata

```bash
substack post metadata <url>
```

Returns the full metadata dictionary for a post.

```bash
substack post metadata https://example.substack.com/p/my-post --pretty
```

### Get content

```bash
substack post content <url>
```

Returns the post URL and its HTML body content.

### Check paywall status

```bash
substack post paywalled <url>
```

Returns whether the post is paywalled.

## User Commands

### Get user info

```bash
substack user info <username>
```

Returns the full user profile data.

### Get subscriptions

```bash
substack user subscriptions <username>
```

Returns the list of newsletters the user is subscribed to.

## Category Commands

### List all categories

```bash
substack categories
```

Returns all available newsletter categories with their names and IDs.

### Get newsletters in a category

```bash
substack category newsletters --name <name> [--metadata]
substack category newsletters --id <id> [--metadata]
```

Returns newsletter URLs in the category. Add `--metadata` to get full newsletter metadata instead.

```bash
# By name
substack category newsletters --name Technology

# By ID with full metadata
substack category newsletters --id 42 --metadata --pretty
```

## Other Commands

### Resolve a renamed handle

```bash
substack resolve-handle <handle>
```

Checks if a Substack user handle has been renamed and returns the new handle.

### Quickstart

```bash
substack quickstart
```

Prints a concise reference guide covering all CLI commands and options.

### Version

```bash
substack version
```

## Authentication

To access paywalled content from the CLI, pass `--cookies` before the command:

```bash
substack --cookies cookies.json post content https://example.substack.com/p/paid-post
substack --cookies cookies.json newsletter posts https://example.substack.com
```

See the [Authentication Guide](authentication.md) for details on obtaining cookies.

## Notes

- API calls include a 2-second delay to be respectful to Substack's servers. Use `--limit` to avoid long waits on large newsletters.
- All output is JSON. Pipe to `jq` for further processing, or use `--pretty` for readability.
- The CLI can also be invoked as `python -m substack_api`.
