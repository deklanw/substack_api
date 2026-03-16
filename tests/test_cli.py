import json
from unittest.mock import MagicMock, patch

import pytest

from substack_api.cli import QUICKSTART_TEXT, _build_parser, main


class TestBuildParser:
    def test_newsletter_posts_args(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["newsletter", "posts", "https://example.substack.com", "--limit", "5"]
        )
        assert args.command == "newsletter"
        assert args.subcommand == "posts"
        assert args.url == "https://example.substack.com"
        assert args.limit == 5

    def test_newsletter_posts_sort(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["newsletter", "posts", "https://example.substack.com", "--sort", "top"]
        )
        assert args.sort == "top"

    def test_newsletter_posts_default_sort(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["newsletter", "posts", "https://example.substack.com"]
        )
        assert args.sort == "new"

    def test_newsletter_search_args(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["newsletter", "search", "https://example.substack.com", "machine learning"]
        )
        assert args.subcommand == "search"
        assert args.query == "machine learning"

    def test_newsletter_podcasts_args(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["newsletter", "podcasts", "https://example.substack.com", "--limit", "3"]
        )
        assert args.subcommand == "podcasts"
        assert args.limit == 3

    def test_newsletter_recs_args(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["newsletter", "recs", "https://example.substack.com"]
        )
        assert args.subcommand == "recs"

    def test_newsletter_authors_args(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["newsletter", "authors", "https://example.substack.com"]
        )
        assert args.subcommand == "authors"

    def test_post_metadata_args(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["post", "metadata", "https://example.substack.com/p/test"]
        )
        assert args.command == "post"
        assert args.subcommand == "metadata"
        assert args.url == "https://example.substack.com/p/test"

    def test_post_content_args(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["post", "content", "https://example.substack.com/p/test"]
        )
        assert args.subcommand == "content"

    def test_post_paywalled_args(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["post", "paywalled", "https://example.substack.com/p/test"]
        )
        assert args.subcommand == "paywalled"

    def test_user_info_args(self):
        parser = _build_parser()
        args = parser.parse_args(["user", "info", "testuser"])
        assert args.command == "user"
        assert args.subcommand == "info"
        assert args.username == "testuser"

    def test_user_subscriptions_args(self):
        parser = _build_parser()
        args = parser.parse_args(["user", "subscriptions", "testuser"])
        assert args.subcommand == "subscriptions"

    def test_categories_args(self):
        parser = _build_parser()
        args = parser.parse_args(["categories"])
        assert args.command == "categories"

    def test_category_newsletters_by_name(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["category", "newsletters", "--name", "Technology"]
        )
        assert args.command == "category"
        assert args.subcommand == "newsletters"
        assert args.name == "Technology"
        assert args.id is None

    def test_category_newsletters_by_id(self):
        parser = _build_parser()
        args = parser.parse_args(["category", "newsletters", "--id", "42"])
        assert args.id == 42
        assert args.name is None

    def test_category_newsletters_metadata_flag(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["category", "newsletters", "--name", "Tech", "--metadata"]
        )
        assert args.metadata is True

    def test_resolve_handle_args(self):
        parser = _build_parser()
        args = parser.parse_args(["resolve-handle", "olduser"])
        assert args.command == "resolve-handle"
        assert args.handle == "olduser"

    def test_global_cookies_option(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["--cookies", "my_cookies.json", "newsletter", "posts", "https://x.substack.com"]
        )
        assert args.cookies == "my_cookies.json"

    def test_global_pretty_option(self):
        parser = _build_parser()
        args = parser.parse_args(
            ["--pretty", "categories"]
        )
        assert args.pretty is True

    def test_quickstart_args(self):
        parser = _build_parser()
        args = parser.parse_args(["quickstart"])
        assert args.command == "quickstart"

    def test_version_args(self):
        parser = _build_parser()
        args = parser.parse_args(["version"])
        assert args.command == "version"


class TestQuickstart:
    def test_quickstart_output(self, capsys):
        with patch("sys.argv", ["substack", "quickstart"]):
            main()
        out = capsys.readouterr().out
        assert "substack newsletter posts" in out
        assert "substack post metadata" in out
        assert "substack user info" in out
        assert "substack categories" in out
        assert "--cookies" in out
        assert "--pretty" in out
        assert "EXAMPLES" in out

    def test_quickstart_text_contains_examples(self):
        assert "substack newsletter search" in QUICKSTART_TEXT
        assert "substack resolve-handle" in QUICKSTART_TEXT


class TestVersion:
    def test_version_output(self, capsys):
        with patch("sys.argv", ["substack", "version"]):
            main()
        out = capsys.readouterr().out.strip()
        assert len(out) > 0


class TestNewsletterCommands:
    @patch("substack_api.cli.Newsletter")
    def test_posts_output(self, MockNewsletter, capsys):
        mock_post = MagicMock()
        mock_post.url = "https://example.substack.com/p/test"
        MockNewsletter.return_value.get_posts.return_value = [mock_post]

        with patch("sys.argv", ["substack", "newsletter", "posts", "https://example.substack.com"]):
            main()

        data = json.loads(capsys.readouterr().out)
        assert data == [{"url": "https://example.substack.com/p/test"}]
        MockNewsletter.return_value.get_posts.assert_called_once_with(
            sorting="new", limit=None
        )

    @patch("substack_api.cli.Newsletter")
    def test_posts_with_sort_and_limit(self, MockNewsletter, capsys):
        MockNewsletter.return_value.get_posts.return_value = []

        with patch("sys.argv", ["substack", "newsletter", "posts", "https://x.substack.com", "--sort", "top", "--limit", "3"]):
            main()

        MockNewsletter.return_value.get_posts.assert_called_once_with(
            sorting="top", limit=3
        )

    @patch("substack_api.cli.Newsletter")
    def test_search_output(self, MockNewsletter, capsys):
        mock_post = MagicMock()
        mock_post.url = "https://example.substack.com/p/result"
        MockNewsletter.return_value.search_posts.return_value = [mock_post]

        with patch("sys.argv", ["substack", "newsletter", "search", "https://example.substack.com", "test query"]):
            main()

        data = json.loads(capsys.readouterr().out)
        assert data == [{"url": "https://example.substack.com/p/result"}]
        MockNewsletter.return_value.search_posts.assert_called_once_with(
            query="test query", limit=None
        )

    @patch("substack_api.cli.Newsletter")
    def test_podcasts_output(self, MockNewsletter, capsys):
        MockNewsletter.return_value.get_podcasts.return_value = []

        with patch("sys.argv", ["substack", "newsletter", "podcasts", "https://x.substack.com"]):
            main()

        data = json.loads(capsys.readouterr().out)
        assert data == []

    @patch("substack_api.cli.Newsletter")
    def test_recs_output(self, MockNewsletter, capsys):
        mock_nl = MagicMock()
        mock_nl.url = "https://rec.substack.com"
        MockNewsletter.return_value.get_recommendations.return_value = [mock_nl]

        with patch("sys.argv", ["substack", "newsletter", "recs", "https://x.substack.com"]):
            main()

        data = json.loads(capsys.readouterr().out)
        assert data == [{"url": "https://rec.substack.com"}]

    @patch("substack_api.cli.Newsletter")
    def test_authors_output(self, MockNewsletter, capsys):
        mock_user = MagicMock()
        mock_user.username = "author1"
        MockNewsletter.return_value.get_authors.return_value = [mock_user]

        with patch("sys.argv", ["substack", "newsletter", "authors", "https://x.substack.com"]):
            main()

        data = json.loads(capsys.readouterr().out)
        assert data == [{"username": "author1"}]


class TestPostCommands:
    @patch("substack_api.cli.Post")
    def test_metadata_output(self, MockPost, capsys):
        MockPost.return_value.get_metadata.return_value = {
            "title": "Test", "id": 123
        }

        with patch("sys.argv", ["substack", "post", "metadata", "https://x.substack.com/p/test"]):
            main()

        data = json.loads(capsys.readouterr().out)
        assert data == {"title": "Test", "id": 123}

    @patch("substack_api.cli.Post")
    def test_content_output(self, MockPost, capsys):
        MockPost.return_value.url = "https://x.substack.com/p/test"
        MockPost.return_value.get_content.return_value = "<p>Hello</p>"

        with patch("sys.argv", ["substack", "post", "content", "https://x.substack.com/p/test"]):
            main()

        data = json.loads(capsys.readouterr().out)
        assert data == {"url": "https://x.substack.com/p/test", "html": "<p>Hello</p>"}

    @patch("substack_api.cli.Post")
    def test_paywalled_output(self, MockPost, capsys):
        MockPost.return_value.url = "https://x.substack.com/p/test"
        MockPost.return_value.is_paywalled.return_value = True

        with patch("sys.argv", ["substack", "post", "paywalled", "https://x.substack.com/p/test"]):
            main()

        data = json.loads(capsys.readouterr().out)
        assert data == {"url": "https://x.substack.com/p/test", "paywalled": True}


class TestUserCommands:
    @patch("substack_api.cli.User")
    def test_info_output(self, MockUser, capsys):
        MockUser.return_value.get_raw_data.return_value = {
            "id": 1, "name": "Test User"
        }

        with patch("sys.argv", ["substack", "user", "info", "testuser"]):
            main()

        data = json.loads(capsys.readouterr().out)
        assert data == {"id": 1, "name": "Test User"}

    @patch("substack_api.cli.User")
    def test_subscriptions_output(self, MockUser, capsys):
        MockUser.return_value.get_subscriptions.return_value = [
            {"publication_name": "Test", "domain": "test.substack.com"}
        ]

        with patch("sys.argv", ["substack", "user", "subscriptions", "testuser"]):
            main()

        data = json.loads(capsys.readouterr().out)
        assert len(data) == 1
        assert data[0]["publication_name"] == "Test"


class TestCategoryCommands:
    @patch("substack_api.cli.list_all_categories")
    def test_categories_output(self, mock_list, capsys):
        mock_list.return_value = [("Technology", 1), ("Culture", 2)]

        with patch("sys.argv", ["substack", "categories"]):
            main()

        data = json.loads(capsys.readouterr().out)
        assert data == [{"name": "Technology", "id": 1}, {"name": "Culture", "id": 2}]

    @patch("substack_api.cli.Category")
    def test_category_newsletters_urls(self, MockCategory, capsys):
        MockCategory.return_value.get_newsletter_urls.return_value = [
            "https://a.substack.com", "https://b.substack.com"
        ]

        with patch("sys.argv", ["substack", "category", "newsletters", "--name", "Tech"]):
            main()

        data = json.loads(capsys.readouterr().out)
        assert data == ["https://a.substack.com", "https://b.substack.com"]

    @patch("substack_api.cli.Category")
    def test_category_newsletters_metadata(self, MockCategory, capsys):
        MockCategory.return_value.get_newsletter_metadata.return_value = [
            {"name": "A", "url": "https://a.substack.com"}
        ]

        with patch("sys.argv", ["substack", "category", "newsletters", "--name", "Tech", "--metadata"]):
            main()

        data = json.loads(capsys.readouterr().out)
        assert data == [{"name": "A", "url": "https://a.substack.com"}]

    @patch("substack_api.cli.Category")
    def test_category_newsletters_by_id(self, MockCategory, capsys):
        MockCategory.return_value.get_newsletter_urls.return_value = []

        with patch("sys.argv", ["substack", "category", "newsletters", "--id", "42"]):
            main()

        MockCategory.assert_called_once_with(name=None, id=42)


class TestResolveHandle:
    @patch("substack_api.cli.resolve_handle_redirect")
    def test_resolve_found(self, mock_resolve, capsys):
        mock_resolve.return_value = "newuser"

        with patch("sys.argv", ["substack", "resolve-handle", "olduser"]):
            main()

        data = json.loads(capsys.readouterr().out)
        assert data == {"old_handle": "olduser", "new_handle": "newuser"}

    @patch("substack_api.cli.resolve_handle_redirect")
    def test_resolve_not_found(self, mock_resolve, capsys):
        mock_resolve.return_value = None

        with patch("sys.argv", ["substack", "resolve-handle", "sameuser"]):
            main()

        data = json.loads(capsys.readouterr().out)
        assert data == {"old_handle": "sameuser", "new_handle": None}


class TestPrettyOutput:
    @patch("substack_api.cli.list_all_categories")
    def test_pretty_flag(self, mock_list, capsys):
        mock_list.return_value = [("Tech", 1)]

        with patch("sys.argv", ["substack", "--pretty", "categories"]):
            main()

        out = capsys.readouterr().out
        # Pretty output has indentation
        assert "  " in out


class TestErrorHandling:
    def test_no_command_shows_help(self, capsys):
        with patch("sys.argv", ["substack"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_newsletter_no_subcommand(self, capsys):
        with patch("sys.argv", ["substack", "newsletter"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_post_no_subcommand(self, capsys):
        with patch("sys.argv", ["substack", "post"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_user_no_subcommand(self, capsys):
        with patch("sys.argv", ["substack", "user"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("substack_api.cli.Newsletter")
    def test_api_error_exits_with_1(self, MockNewsletter, capsys):
        MockNewsletter.return_value.get_posts.side_effect = Exception("API Error")

        with patch("sys.argv", ["substack", "newsletter", "posts", "https://x.substack.com"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        assert "Error" in capsys.readouterr().err


class TestAuthIntegration:
    @patch("substack_api.cli.Post")
    @patch("substack_api.cli.SubstackAuth")
    def test_cookies_passed_to_post(self, MockAuth, MockPost, capsys):
        mock_auth = MagicMock()
        MockAuth.return_value = mock_auth
        MockPost.return_value.get_metadata.return_value = {"title": "Test"}

        with patch("sys.argv", ["substack", "--cookies", "cookies.json", "post", "metadata", "https://x.substack.com/p/test"]):
            main()

        MockAuth.assert_called_once_with("cookies.json")
        MockPost.assert_called_once_with("https://x.substack.com/p/test", auth=mock_auth)
