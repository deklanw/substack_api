# Installation

## Requirements

- Python 3.12 or higher
- pip or uv (Python package installer)

## Install from PyPI

The simplest way to install the Substack API library is via pip:

```bash
pip install substack-api
```

## Install from Source

Alternatively, you can install from source:

```bash
git clone https://github.com/nhagar/substack_api.git
cd substack_api
pip install -e .
```

## Dependencies

The library has minimal dependencies:
- `curl_cffi` - For asynchronous HTTP requests

These dependencies will be automatically installed when you install the package.

## CLI

Installing the package also installs the `substack` command-line tool:

```bash
substack --help
substack quickstart
```

See the [CLI Guide](cli.md) for full documentation.
