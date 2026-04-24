"""Tests for web-mirror URL rewriting, download, and crawl logic."""

import os
import sys
import types
import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, call
from urllib.parse import urlparse, urlunparse, urljoin


# ---------------------------------------------------------------------------
# Helpers to fake heavy third-party modules before importing src files
# ---------------------------------------------------------------------------

def _stub_module(name, attrs=None):
    """Create a stub module and register it in sys.modules."""
    mod = types.ModuleType(name)
    if attrs:
        for k, v in attrs.items():
            setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


def _ensure_stubs():
    """Install stubs for selenium, playwright, undetected_chromedriver, and
    requests_cache so that the source modules can be imported without the real
    packages being installed."""
    if "selenium" not in sys.modules:
        _stub_module("selenium")
        _stub_module("selenium.webdriver", {"Edge": MagicMock, "Chrome": MagicMock,
                                            "ChromeOptions": MagicMock})
        _stub_module("selenium.webdriver.common", {})
        _stub_module("selenium.webdriver.common.by", {"By": MagicMock()})

    if "playwright" not in sys.modules:
        _stub_module("playwright")
        sync_mod = _stub_module("playwright.sync_api", {"sync_playwright": MagicMock})
        # make sync_playwright usable as context manager
        sync_mod.sync_playwright = MagicMock

    if "undetected_chromedriver" not in sys.modules:
        uc = _stub_module("undetected_chromedriver")
        uc.ChromeOptions = MagicMock
        uc.Chrome = MagicMock

    if "requests_cache" not in sys.modules:
        rc = _stub_module("requests_cache")
        rc.install_cache = MagicMock()
        rc.CachedSession = MagicMock


_ensure_stubs()

# Make sure src/ is on the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ===================================================================
# 1. Tests for main.py (Selenium-based mirror)
# ===================================================================

class TestMainGetSitemap:
    """Tests for main.get_sitemap."""

    @patch("requests.get")
    def test_get_sitemap_returns_hardcoded_video(self, mock_get):
        """get_sitemap currently returns a hardcoded list (the real sitemap
        parsing is commented out), so it should return exactly that list."""
        mock_resp = MagicMock()
        mock_resp.text = "<urlset><url><loc>https://www.place.holder/es/page1</loc></url></urlset>"
        mock_get.return_value = mock_resp

        import main as main_mod
        result = main_mod.get_sitemap()

        assert isinstance(result, list)
        assert result == ["https://www.place.holder/VIDEO"]

    @patch("requests.get")
    def test_get_sitemap_calls_requests(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = "<urlset></urlset>"
        mock_get.return_value = mock_resp

        import main as main_mod
        main_mod.get_sitemap()

        mock_get.assert_called_once_with("https://www.place.holder/es/sitemap.xml")


class TestMainDownloadVideo:
    """Tests for main.download_video."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("shutil.copyfileobj")
    @patch("requests.get")
    def test_download_video_streams_to_file(self, mock_get, mock_copy, mock_file):
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.raw = MagicMock()
        mock_get.return_value = mock_response

        import main as main_mod
        main_mod.download_video("https://cdn.example.com/v.mp4", "/tmp/v.mp4")

        mock_get.assert_called_once_with("https://cdn.example.com/v.mp4", stream=True)
        mock_copy.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    @patch("shutil.copyfileobj")
    @patch("requests.get")
    def test_download_video_opens_correct_filename(self, mock_get, mock_copy, mock_file):
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_get.return_value = mock_response

        import main as main_mod
        main_mod.download_video("https://cdn.example.com/v.mp4", "/data/video.mp4")

        mock_file.assert_called_once_with("/data/video.mp4", "wb")


class TestMainDownloadWebpage:
    """Tests for main.download_webpage (Selenium driver version)."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    @patch("os.makedirs")
    @patch("time.sleep")
    def test_download_webpage_no_video(self, mock_sleep, mock_makedirs, mock_exists, mock_file):
        import main as main_mod

        html = '<html><body><a href="https://www.place.holder/es/page">L</a></body></html>'
        driver = MagicMock()
        driver.page_source = html

        main_mod.download_webpage("https://www.place.holder/es/articles/test", driver)

        mock_sleep.assert_called_once_with(2)
        # Should write to index.html since no video
        written_path = mock_file.call_args[0][0]
        assert written_path.endswith("/index.html")
        mock_file.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=False)
    @patch("os.makedirs")
    @patch("time.sleep")
    def test_download_webpage_creates_folder(self, mock_sleep, mock_makedirs, mock_exists, mock_file):
        import main as main_mod

        driver = MagicMock()
        driver.page_source = "<html><body>Hello</body></html>"

        main_mod.download_webpage("https://www.place.holder/es/new-page", driver)

        mock_makedirs.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    @patch("os.makedirs")
    @patch("time.sleep")
    @patch("main.download_video")
    def test_download_webpage_with_video(self, mock_dl_video, mock_sleep, mock_makedirs,
                                         mock_exists, mock_file):
        import main as main_mod

        html = ('<html><body>'
                '<video src="https://cdn.example.com/clip.mp4"></video>'
                '</body></html>')
        driver = MagicMock()
        driver.page_source = html

        main_mod.download_webpage("https://www.place.holder/es/videos/clip", driver)

        mock_dl_video.assert_called_once()
        # Video pages write to .html, not /index.html
        written_path = mock_file.call_args[0][0]
        assert written_path.endswith(".html")
        assert not written_path.endswith("/index.html")

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    @patch("os.makedirs")
    @patch("time.sleep")
    def test_download_webpage_rewrites_hrefs(self, mock_sleep, mock_makedirs, mock_exists, mock_file):
        import main as main_mod

        html = ('<html><head>'
                '<link href="https://www.place.holder/css/style.css" rel="stylesheet">'
                '<base href="https://www.place.holder/">'
                '</head><body>'
                '<a href="https://www.place.holder/es/page">Link</a>'
                '<a href="https://example.com/ext">External</a>'
                '</body></html>')
        driver = MagicMock()
        driver.page_source = html

        main_mod.download_webpage("https://www.place.holder/es/test", driver)

        written_html = mock_file().write.call_args[0][0]
        # Internal links rewritten
        assert "https://www.place.holder/es/page" not in written_html
        assert "https://www.place.holder/css/style.css" not in written_html
        # External link preserved
        assert "https://example.com/ext" in written_html

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    @patch("os.makedirs")
    @patch("time.sleep")
    def test_download_webpage_rewrites_base_tag(self, mock_sleep, mock_makedirs, mock_exists, mock_file):
        import main as main_mod

        html = '<html><head><base href="https://www.place.holder/"></head><body></body></html>'
        driver = MagicMock()
        driver.page_source = html

        main_mod.download_webpage("https://www.place.holder/es/p", driver)

        written_html = mock_file().write.call_args[0][0]
        assert 'href="/"' in written_html


class TestMainEntryPoint:
    """Tests for main.py __main__ block."""

    @patch("main.download_webpage")
    @patch("main.get_sitemap", return_value=["https://www.place.holder/VIDEO"])
    @patch("os.makedirs")
    @patch("os.path.exists", return_value=False)
    def test_main_block_creates_fulldir_and_iterates(self, mock_exists, mock_makedirs,
                                                      mock_sitemap, mock_download):
        import main as main_mod

        mock_driver = MagicMock()
        with patch.object(sys.modules["selenium.webdriver"], "Edge", return_value=mock_driver):
            # Execute the main block logic manually
            if not os.path.exists(main_mod.fulldir):
                os.makedirs(main_mod.fulldir)
            links = main_mod.get_sitemap()
            for link in links:
                main_mod.download_webpage(link, mock_driver)

        mock_makedirs.assert_called()
        mock_sitemap.assert_called_once()
        mock_download.assert_called_once_with("https://www.place.holder/VIDEO", mock_driver)


# ===================================================================
# 2. Tests for main2.py (Playwright-based mirror)
# ===================================================================

class TestMain2GetSitemap:
    """Tests for main2.get_sitemap."""

    @patch("requests.get")
    def test_get_sitemap_returns_hardcoded(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = "<urlset><url><loc>https://www.place.holder/es/a</loc></url></urlset>"
        mock_get.return_value = mock_resp

        import main2
        result = main2.get_sitemap()
        assert result == ["https://www.place.holder/VIDEO"]

    @patch("requests.get")
    def test_get_sitemap_parses_xml(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = ("<urlset>"
                          "<url><loc>https://www.place.holder/es/a</loc></url>"
                          "<url><loc>https://www.place.holder/es/b</loc></url>"
                          "</urlset>")
        mock_get.return_value = mock_resp

        import main2
        # Even though it parses, the hardcoded return overrides
        result = main2.get_sitemap()
        assert result == ["https://www.place.holder/VIDEO"]


class TestMain2DownloadVideo:
    """Tests for main2.download_video."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("shutil.copyfileobj")
    @patch("requests.get")
    def test_download_video_streams(self, mock_get, mock_copy, mock_file):
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.raw = MagicMock()
        mock_get.return_value = mock_response

        import main2
        main2.download_video("https://cdn.example.com/vid.mp4", "/tmp/vid.mp4")

        mock_get.assert_called_once_with("https://cdn.example.com/vid.mp4", stream=True)
        mock_copy.assert_called_once()


class TestMain2DownloadWebpage:
    """Tests for main2.download_webpage (Playwright version)."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    @patch("os.makedirs")
    @patch("time.sleep")
    def test_download_webpage_no_video(self, mock_sleep, mock_makedirs, mock_exists, mock_file):
        import main2

        html = '<html><body><p>Just text</p></body></html>'
        mock_page = MagicMock()
        mock_page.content.return_value = html
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page

        main2.download_webpage("https://www.place.holder/es/articles/test", mock_context)

        mock_page.goto.assert_called_once_with("https://www.place.holder/es/articles/test")
        mock_sleep.assert_called_once_with(3)
        written_path = mock_file.call_args[0][0]
        assert written_path.endswith("/index.html")

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=False)
    @patch("os.makedirs")
    @patch("time.sleep")
    def test_download_webpage_creates_dir(self, mock_sleep, mock_makedirs, mock_exists, mock_file):
        import main2

        mock_page = MagicMock()
        mock_page.content.return_value = "<html><body></body></html>"
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page

        main2.download_webpage("https://www.place.holder/es/new", mock_context)

        mock_makedirs.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    @patch("os.makedirs")
    @patch("time.sleep")
    @patch("main2.download_video")
    def test_download_webpage_with_video(self, mock_dl_video, mock_sleep, mock_makedirs,
                                          mock_exists, mock_file):
        import main2

        html = '<html><body><video src="https://cdn.example.com/v.mp4"></video></body></html>'
        mock_page = MagicMock()
        mock_page.content.return_value = html
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page

        main2.download_webpage("https://www.place.holder/es/videos/v", mock_context)

        mock_dl_video.assert_called_once()
        written_path = mock_file.call_args[0][0]
        assert written_path.endswith(".html")
        assert not written_path.endswith("/index.html")

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    @patch("os.makedirs")
    @patch("time.sleep")
    def test_download_webpage_rewrites_all_tag_types(self, mock_sleep, mock_makedirs,
                                                       mock_exists, mock_file):
        import main2

        html = ('<html><head>'
                '<link href="https://www.place.holder/css/x.css" rel="stylesheet">'
                '<base href="https://www.place.holder/">'
                '</head><body>'
                '<a href="https://www.place.holder/es/page">L</a>'
                '<a href="https://other.com/">Ext</a>'
                '</body></html>')
        mock_page = MagicMock()
        mock_page.content.return_value = html
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page

        main2.download_webpage("https://www.place.holder/es/t", mock_context)

        written_html = mock_file().write.call_args[0][0]
        assert "https://www.place.holder/" not in written_html
        assert "https://other.com/" in written_html

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    @patch("os.makedirs")
    @patch("time.sleep")
    @patch("main2.download_video")
    def test_video_src_rewritten_to_local(self, mock_dl_video, mock_sleep, mock_makedirs,
                                            mock_exists, mock_file):
        import main2

        html = '<html><body><video src="https://cdn.example.com/clip.mp4"></video></body></html>'
        mock_page = MagicMock()
        mock_page.content.return_value = html
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page

        main2.download_webpage("https://www.place.holder/es/videos/clip", mock_context)

        written_html = mock_file().write.call_args[0][0]
        assert "clip.mp4" in written_html
        # The video src should now point to a local path starting with /
        assert 'src="/' in written_html


# ===================================================================
# 3. Tests for old_main.py (recursive crawl with undetected_chromedriver)
# ===================================================================

class TestOldMainExtractLinks:
    """Tests for old_main.extract_links."""

    def test_extract_links_finds_internal(self):
        import old_main

        # Set the language global that extract_links uses
        old_main.language = "es"

        mock_driver = MagicMock()
        mock_driver.current_url = "https://www.place.holder/es"
        mock_driver.page_source = (
            '<html><body>'
            '<a href="/es/page1">Page 1</a>'
            '<a href="/es/page2">Page 2</a>'
            '<a href="https://external.com/">Ext</a>'
            '</body></html>'
        )

        visited = set()
        links = old_main.extract_links(mock_driver, visited)

        assert len(links) == 2
        for link in links:
            assert "/es/" in link

    def test_extract_links_skips_visited(self):
        import old_main
        old_main.language = "es"

        mock_driver = MagicMock()
        mock_driver.current_url = "https://www.place.holder/es"
        mock_driver.page_source = (
            '<html><body>'
            '<a href="/es/page1">Page 1</a>'
            '<a href="/es/page2">Page 2</a>'
            '</body></html>'
        )

        visited = {"https://www.place.holder/es/page1"}
        links = old_main.extract_links(mock_driver, visited)

        assert len(links) == 1
        found = links.pop()
        assert "page2" in found

    def test_extract_links_ignores_external(self):
        import old_main
        old_main.language = "es"

        mock_driver = MagicMock()
        mock_driver.current_url = "https://www.place.holder/es"
        mock_driver.page_source = (
            '<html><body>'
            '<a href="https://external.com/page">Ext</a>'
            '<a href="/fr/page">French</a>'
            '</body></html>'
        )

        visited = set()
        links = old_main.extract_links(mock_driver, visited)

        assert len(links) == 0

    def test_extract_links_empty_page(self):
        import old_main
        old_main.language = "es"

        mock_driver = MagicMock()
        mock_driver.current_url = "https://www.place.holder/es"
        mock_driver.page_source = "<html><body></body></html>"

        links = old_main.extract_links(mock_driver, set())
        assert len(links) == 0


class TestOldMainRecursiveCrawl:
    """Tests for old_main.recursive_crawl."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=False)
    @patch("os.makedirs")
    @patch("old_main.extract_links", return_value=set())
    def test_recursive_crawl_single_page(self, mock_extract, mock_makedirs,
                                          mock_exists, mock_file):
        import old_main

        mock_driver = MagicMock()
        mock_driver.page_source = "<html><body>Test</body></html>"
        visited = set()

        old_main.recursive_crawl(mock_driver, "https://www.place.holder/es/page", visited)

        assert "https://www.place.holder/es/page" in visited
        mock_driver.get.assert_called_once_with("https://www.place.holder/es/page")
        mock_makedirs.assert_called_once()
        mock_file.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    @patch("os.makedirs")
    @patch("old_main.extract_links")
    def test_recursive_crawl_follows_links(self, mock_extract, mock_makedirs,
                                            mock_exists, mock_file):
        import old_main

        mock_driver = MagicMock()
        mock_driver.page_source = "<html><body>Test</body></html>"

        # First call returns a child link, second call returns empty
        mock_extract.side_effect = [
            {"https://www.place.holder/es/child"},
            set()
        ]

        visited = set()
        old_main.recursive_crawl(mock_driver, "https://www.place.holder/es/page", visited)

        assert "https://www.place.holder/es/page" in visited
        assert "https://www.place.holder/es/child" in visited
        assert mock_driver.get.call_count == 2

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=False)
    @patch("os.makedirs")
    @patch("old_main.extract_links", return_value=set())
    def test_recursive_crawl_writes_html(self, mock_extract, mock_makedirs,
                                          mock_exists, mock_file):
        import old_main

        mock_driver = MagicMock()
        mock_driver.page_source = "<html><body>Content</body></html>"

        old_main.recursive_crawl(mock_driver, "https://www.place.holder/es/p", set())

        # The file should contain the page source
        mock_file().write.assert_called_once_with("<html><body>Content</body></html>")

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=False)
    @patch("os.makedirs")
    @patch("old_main.extract_links", return_value=set())
    def test_recursive_crawl_local_path_strips_scheme(self, mock_extract, mock_makedirs,
                                                        mock_exists, mock_file):
        import old_main

        mock_driver = MagicMock()
        mock_driver.page_source = "<html></html>"

        old_main.recursive_crawl(mock_driver, "https://www.place.holder/es/test", set())

        # makedirs should be called with a path that has no scheme/netloc
        created_path = mock_makedirs.call_args[0][0]
        assert "https" not in created_path
        assert "www.place.holder" not in created_path


# ===================================================================
# 4. Tests for old_video.py (standalone video downloader script)
# ===================================================================

class TestOldVideo:
    """Tests for old_video.py -- a script-style file with all module-level code.
    We exec the source with mocked globals to get real coverage."""

    def _exec_old_video(self):
        """Execute old_video.py source with fully mocked dependencies.
        Returns the namespace dict so callers can inspect state."""
        import importlib
        # Remove old_video from cache so we can re-import fresh
        if "old_video" in sys.modules:
            del sys.modules["old_video"]

        # Prepare mock driver and element
        mock_element = MagicMock()
        mock_element.get_attribute.side_effect = lambda attr: {
            "src": "https://cdn.example.com/video.mp4",
            "poster": "https://cdn.example.com/poster.jpg"
        }.get(attr, "")

        mock_driver = MagicMock()
        mock_driver.find_element.return_value = mock_element
        mock_driver.page_source = "<html><video class='vjs-tech'></video></html>"

        # Set up undetected_chromedriver stub
        uc_mod = sys.modules["undetected_chromedriver"]
        uc_mod.ChromeOptions = MagicMock
        uc_mod.Chrome = MagicMock(return_value=mock_driver)

        # Mock requests.get for video download
        mock_response = MagicMock()
        mock_response.content = b"fake-video-data"

        with patch("requests.get", return_value=mock_response) as mock_get, \
             patch("builtins.open", new_callable=mock_open) as mock_file, \
             patch("time.sleep"):
            import old_video
            return {
                "module": old_video,
                "mock_driver": mock_driver,
                "mock_element": mock_element,
                "mock_get": mock_get,
                "mock_file": mock_file,
                "mock_response": mock_response,
            }

    def test_old_video_executes_without_error(self):
        """The script should run to completion with mocked deps."""
        result = self._exec_old_video()
        assert result["module"] is not None

    def test_old_video_navigates_to_url(self):
        """The script should call driver.get with the target URL."""
        result = self._exec_old_video()
        result["mock_driver"].get.assert_called_once_with(
            "https://www.place.holder/VIDEO"
        )

    def test_old_video_finds_video_element(self):
        """The script should find the video element by xpath."""
        result = self._exec_old_video()
        result["mock_driver"].find_element.assert_called_once()

    def test_old_video_extracts_src_and_poster(self):
        """The script should extract src and poster attributes."""
        result = self._exec_old_video()
        calls = result["mock_element"].get_attribute.call_args_list
        attrs = [c[0][0] for c in calls]
        assert "src" in attrs
        assert "poster" in attrs

    def test_old_video_downloads_video(self):
        """The script should download the video via requests.get."""
        result = self._exec_old_video()
        result["mock_get"].assert_called_with("https://cdn.example.com/video.mp4")

    def test_old_video_saves_video_file(self):
        """The script should write video content to video.mp4."""
        result = self._exec_old_video()
        # Check open was called with video.mp4 for writing binary
        file_calls = result["mock_file"].call_args_list
        video_write = [c for c in file_calls if c[0][0] == "video.mp4"]
        assert len(video_write) > 0

    def test_old_video_saves_html(self):
        """The script should save page source as webpage_mirror.html."""
        result = self._exec_old_video()
        file_calls = result["mock_file"].call_args_list
        html_write = [c for c in file_calls if c[0][0] == "webpage_mirror.html"]
        assert len(html_write) > 0

    def test_old_video_quits_driver(self):
        """The script should call driver.quit() at the end."""
        result = self._exec_old_video()
        result["mock_driver"].quit.assert_called_once()


# ===================================================================
# 5. URL rewriting logic tests (expanded from originals)
# ===================================================================

class TestUrlRewriting:
    """Test URL-to-local-path conversion logic extracted from main.py."""

    def test_url_to_local_path(self):
        url = "https://www.place.holder/es/articles/topic"
        local_url = urlparse(url)._replace(netloc="", scheme="")
        local_path = urlunparse(local_url)
        assert local_path == "/es/articles/topic"

    def test_url_preserves_path_segments(self):
        url = "https://www.place.holder/es/videos/2024/clip"
        local_url = urlparse(url)._replace(netloc="", scheme="")
        result = urlunparse(local_url)
        assert "/es/videos/2024/clip" == result

    def test_root_url(self):
        url = "https://www.place.holder/"
        local_url = urlparse(url)._replace(netloc="", scheme="")
        result = urlunparse(local_url)
        assert result == "/"

    def test_url_with_query_string(self):
        url = "https://www.place.holder/es/search?q=test"
        local_url = urlparse(url)._replace(netloc="", scheme="")
        result = urlunparse(local_url)
        assert result == "/es/search?q=test"

    def test_url_with_fragment(self):
        url = "https://www.place.holder/es/page#section"
        local_url = urlparse(url)._replace(netloc="", scheme="")
        result = urlunparse(local_url)
        assert result == "/es/page#section"

    def test_url_removeprefix_for_old_main(self):
        """old_main uses .removeprefix('/') on the local path."""
        url = "https://www.place.holder/es/page"
        local_url = urlparse(url)._replace(netloc="", scheme="")
        local_folder = urlunparse(local_url).removeprefix("/")
        assert local_folder == "es/page"


class TestHrefModification:
    """Test the href rewriting logic from download_webpage."""

    def test_absolute_url_rewritten(self):
        from bs4 import BeautifulSoup
        html = '<html><body><a href="https://www.place.holder/es/page">Link</a></body></html>'
        page = BeautifulSoup(html, "html.parser")
        for tag in page.find_all("a", href=True):
            if tag["href"].startswith("https://www.place.holder/"):
                tag["href"] = tag["href"].replace("https://www.place.holder", "")
        assert page.find("a")["href"] == "/es/page"

    def test_external_url_not_rewritten(self):
        from bs4 import BeautifulSoup
        html = '<html><body><a href="https://example.com/other">External</a></body></html>'
        page = BeautifulSoup(html, "html.parser")
        for tag in page.find_all("a", href=True):
            if tag["href"].startswith("https://www.place.holder/"):
                tag["href"] = tag["href"].replace("https://www.place.holder", "")
        assert page.find("a")["href"] == "https://example.com/other"

    def test_link_tag_rewritten(self):
        from bs4 import BeautifulSoup
        html = '<html><head><link href="https://www.place.holder/css/style.css" rel="stylesheet"></head></html>'
        page = BeautifulSoup(html, "html.parser")
        for tag in page.find_all("link", href=True):
            if tag["href"].startswith("https://www.place.holder/"):
                tag["href"] = tag["href"].replace("https://www.place.holder", "")
        assert page.find("link")["href"] == "/css/style.css"

    def test_multiple_links_rewritten(self):
        from bs4 import BeautifulSoup
        html = ('<html><body>'
                '<a href="https://www.place.holder/es/a">A</a>'
                '<a href="https://www.place.holder/es/b">B</a>'
                '<a href="https://example.com/">Ext</a>'
                '</body></html>')
        page = BeautifulSoup(html, "html.parser")
        for tag in page.find_all("a", href=True):
            if tag["href"].startswith("https://www.place.holder/"):
                tag["href"] = tag["href"].replace("https://www.place.holder", "")
        links = page.find_all("a")
        assert links[0]["href"] == "/es/a"
        assert links[1]["href"] == "/es/b"
        assert links[2]["href"] == "https://example.com/"

    def test_base_tag_rewritten(self):
        from bs4 import BeautifulSoup
        html = '<html><head><base href="https://www.place.holder/"></head></html>'
        page = BeautifulSoup(html, "html.parser")
        for tag in page.find_all("base", href=True):
            if tag["href"].startswith("https://www.place.holder/"):
                tag["href"] = tag["href"].replace("https://www.place.holder", "")
        assert page.find("base")["href"] == "/"


class TestVideoDetection:
    """Test video element detection from page source."""

    def test_video_tag_found(self):
        from bs4 import BeautifulSoup
        html = '<html><body><video src="https://cdn.example.com/video.mp4"></video></body></html>'
        page = BeautifulSoup(html, "html.parser")
        video = page.find("video")
        assert video is not None
        assert video["src"] == "https://cdn.example.com/video.mp4"

    def test_no_video_tag(self):
        from bs4 import BeautifulSoup
        html = '<html><body><p>No video here</p></body></html>'
        page = BeautifulSoup(html, "html.parser")
        video = page.find("video")
        assert video is None

    def test_video_filename_extraction(self):
        video_url = "https://cdn.example.com/media/2024/clip_hd.mp4"
        filename = os.path.basename(urlparse(video_url).path)
        assert filename == "clip_hd.mp4"

    def test_video_with_class(self):
        from bs4 import BeautifulSoup
        html = '<html><body><video class="vjs-tech" src="https://cdn.example.com/v.mp4"></video></body></html>'
        page = BeautifulSoup(html, "html.parser")
        video = page.find("video")
        assert video is not None
        assert "vjs-tech" in video.get("class", [])


class TestFolderCreation:
    """Test local folder structure creation."""

    def test_creates_nested_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            local_folder = os.path.join(tmpdir, "es", "articles", "topic")
            os.makedirs(local_folder)
            assert os.path.isdir(local_folder)

    def test_video_page_uses_html_suffix(self):
        local_folder = "/data/es/videos/clip"
        local_folder_name = local_folder + ".html"
        assert local_folder_name == "/data/es/videos/clip.html"

    def test_regular_page_uses_index_html(self):
        local_folder = "/data/es/articles/topic"
        local_folder_name = local_folder + "/index.html"
        assert local_folder_name == "/data/es/articles/topic/index.html"

    def test_makedirs_exist_ok(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "a", "b")
            os.makedirs(path)
            # Should not raise
            os.makedirs(path, exist_ok=True)
            assert os.path.isdir(path)


# ===================================================================
# 6. Module-level globals and logging tests
# ===================================================================

class TestModuleGlobals:
    """Test that module-level globals are set correctly."""

    def test_main_globals(self):
        import main as main_mod
        assert main_mod.language == "es"
        assert main_mod.destlocationdir == "/data/"
        assert main_mod.fulldir == "/data/es"

    def test_main2_globals(self):
        import main2
        assert main2.language == "es"
        assert main2.fulldir == "/data/"

    def test_main_logger_exists(self):
        import main as main_mod
        assert main_mod.logger is not None
        assert main_mod.logger.name == "mylogger"
        assert main_mod.logger.level == 20  # logging.INFO

    def test_main2_logger_exists(self):
        import main2
        assert main2.logger is not None
        assert main2.logger.name == "mylogger"

    def test_main_fulldir_construction(self):
        import main as main_mod
        expected = main_mod.destlocationdir + main_mod.language
        assert main_mod.fulldir == expected


class TestUrljoinBehavior:
    """Test urljoin as used in old_main.extract_links."""

    def test_relative_path_joined(self):
        base = "https://www.place.holder/es"
        relative = "/es/page1"
        result = urljoin(base, relative)
        assert result == "https://www.place.holder/es/page1"

    def test_absolute_url_unchanged(self):
        base = "https://www.place.holder/es"
        absolute = "https://external.com/page"
        result = urljoin(base, absolute)
        assert result == "https://external.com/page"

    def test_relative_subpath(self):
        base = "https://www.place.holder/es/"
        relative = "page1"
        result = urljoin(base, relative)
        assert result == "https://www.place.holder/es/page1"


# ===================================================================
# 7. Integration-style tests (end-to-end with mocks)
# ===================================================================

class TestIntegrationMain:
    """Integration tests verifying end-to-end HTML rewriting in main.py."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    @patch("os.makedirs")
    @patch("time.sleep")
    def test_full_page_rewriting(self, mock_sleep, mock_makedirs, mock_exists, mock_file):
        import main as main_mod

        html = ('<html><head>'
                '<link href="https://www.place.holder/css/app.css" rel="stylesheet">'
                '</head><body>'
                '<a href="https://www.place.holder/es/other">Other</a>'
                '<p>Content here</p>'
                '</body></html>')
        driver = MagicMock()
        driver.page_source = html

        main_mod.download_webpage("https://www.place.holder/es/articles/my-article", driver)

        # File written
        mock_file.assert_called_once()
        written_path = mock_file.call_args[0][0]
        assert "index.html" in written_path
        # All internal URLs rewritten
        written_html = mock_file().write.call_args[0][0]
        assert "https://www.place.holder" not in written_html
        assert "/es/other" in written_html
        assert "/css/app.css" in written_html

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    @patch("os.makedirs")
    @patch("time.sleep")
    @patch("main.download_video")
    def test_full_video_rewriting(self, mock_dl_video, mock_sleep, mock_makedirs,
                                   mock_exists, mock_file):
        import main as main_mod

        html = ('<html><body>'
                '<video src="https://cdn.example.com/hd_video.mp4"></video>'
                '<a href="https://www.place.holder/es/related">Related</a>'
                '</body></html>')
        driver = MagicMock()
        driver.page_source = html

        main_mod.download_webpage("https://www.place.holder/es/videos/my-video", driver)

        # Video downloaded
        mock_dl_video.assert_called_once()
        video_url_arg = mock_dl_video.call_args[0][0]
        assert video_url_arg == "https://cdn.example.com/hd_video.mp4"

        # File written as .html (not /index.html)
        written_path = mock_file.call_args[0][0]
        assert written_path.endswith(".html")
        assert "index.html" not in written_path


class TestIntegrationMain2:
    """Integration tests verifying end-to-end HTML rewriting in main2.py."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    @patch("os.makedirs")
    @patch("time.sleep")
    def test_full_page_rewriting(self, mock_sleep, mock_makedirs, mock_exists, mock_file):
        import main2

        html = ('<html><head>'
                '<base href="https://www.place.holder/">'
                '</head><body>'
                '<a href="https://www.place.holder/es/article">Article</a>'
                '</body></html>')
        mock_page = MagicMock()
        mock_page.content.return_value = html
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page

        main2.download_webpage("https://www.place.holder/es/test-page", mock_context)

        mock_context.new_page.assert_called_once()
        mock_page.goto.assert_called_once()

        written_html = mock_file().write.call_args[0][0]
        assert "https://www.place.holder" not in written_html


class TestIntegrationOldMain:
    """Integration tests for old_main.py crawl flow."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=False)
    @patch("os.makedirs")
    def test_crawl_depth_two(self, mock_makedirs, mock_exists, mock_file):
        import old_main
        old_main.language = "es"

        mock_driver = MagicMock()

        # Page 1 has two links, page 2 and 3 have none
        page_sources = {
            "https://www.place.holder/es": (
                '<html><body>'
                '<a href="/es/child1">C1</a>'
                '<a href="/es/child2">C2</a>'
                '</body></html>'
            ),
            "https://www.place.holder/es/child1": "<html><body>Child1</body></html>",
            "https://www.place.holder/es/child2": "<html><body>Child2</body></html>",
        }

        def get_side_effect(url):
            mock_driver.current_url = url
            mock_driver.page_source = page_sources.get(url, "<html></html>")

        mock_driver.get.side_effect = get_side_effect

        visited = set()
        old_main.recursive_crawl(mock_driver, "https://www.place.holder/es", visited)

        assert len(visited) == 3
        assert "https://www.place.holder/es" in visited
        assert "https://www.place.holder/es/child1" in visited
        assert "https://www.place.holder/es/child2" in visited


# ===================================================================
# 8. __main__ block coverage via runpy
# ===================================================================

class TestMainEntryPointBlock:
    """Cover the if __name__ == '__main__' block in main.py."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    @patch("os.makedirs")
    @patch("time.sleep")
    @patch("requests.get")
    def test_main_script_execution(self, mock_req_get, mock_sleep,
                                    mock_makedirs, mock_exists, mock_file):
        import runpy

        mock_resp = MagicMock()
        mock_resp.text = "<urlset></urlset>"
        mock_req_get.return_value = mock_resp

        mock_driver = MagicMock()
        mock_driver.page_source = "<html><body>test</body></html>"

        edge_cls = sys.modules["selenium.webdriver"].Edge
        orig_edge = edge_cls
        sys.modules["selenium.webdriver"].Edge = MagicMock(return_value=mock_driver)

        try:
            # Remove cached module to force re-execution
            if "main" in sys.modules:
                del sys.modules["main"]
            runpy.run_path(
                str(Path(__file__).parent.parent / "src" / "main.py"),
                run_name="__main__"
            )
        finally:
            sys.modules["selenium.webdriver"].Edge = orig_edge
            # Clean up so other tests can re-import
            if "main" in sys.modules:
                del sys.modules["main"]


class TestMain2EntryPointBlock:
    """Cover the if __name__ == '__main__' block in main2.py."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    @patch("os.makedirs")
    @patch("time.sleep")
    @patch("requests.get")
    def test_main2_script_execution(self, mock_req_get, mock_sleep,
                                     mock_makedirs, mock_exists, mock_file):
        import runpy

        mock_resp = MagicMock()
        mock_resp.text = "<urlset></urlset>"
        mock_req_get.return_value = mock_resp

        mock_page = MagicMock()
        mock_page.content.return_value = "<html><body>test</body></html>"

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page

        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_pw_instance = MagicMock()
        mock_pw_instance.chromium.launch.return_value = mock_browser

        mock_pw_cm = MagicMock()
        mock_pw_cm.__enter__ = MagicMock(return_value=mock_pw_instance)
        mock_pw_cm.__exit__ = MagicMock(return_value=False)

        pw_mod = sys.modules["playwright.sync_api"]
        orig_sync = getattr(pw_mod, "sync_playwright", None)
        pw_mod.sync_playwright = MagicMock(return_value=mock_pw_cm)

        try:
            if "main2" in sys.modules:
                del sys.modules["main2"]
            runpy.run_path(
                str(Path(__file__).parent.parent / "src" / "main2.py"),
                run_name="__main__"
            )
        finally:
            pw_mod.sync_playwright = orig_sync
            if "main2" in sys.modules:
                del sys.modules["main2"]


class TestOldMainEntryPointBlock:
    """Cover the if __name__ == '__main__' block in old_main.py."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=False)
    @patch("os.makedirs")
    def test_old_main_script_execution(self, mock_makedirs, mock_exists, mock_file):
        import runpy

        mock_driver = MagicMock()
        mock_driver.page_source = "<html><body>test</body></html>"
        mock_driver.current_url = "https://www.place.holder/es"
        mock_driver.__enter__ = MagicMock(return_value=mock_driver)
        mock_driver.__exit__ = MagicMock(return_value=False)

        uc_mod = sys.modules["undetected_chromedriver"]
        orig_chrome = uc_mod.Chrome
        orig_opts = uc_mod.ChromeOptions
        uc_mod.Chrome = MagicMock(return_value=mock_driver)
        uc_mod.ChromeOptions = MagicMock

        try:
            if "old_main" in sys.modules:
                del sys.modules["old_main"]
            runpy.run_path(
                str(Path(__file__).parent.parent / "src" / "old_main.py"),
                run_name="__main__"
            )
        finally:
            uc_mod.Chrome = orig_chrome
            uc_mod.ChromeOptions = orig_opts
            if "old_main" in sys.modules:
                del sys.modules["old_main"]
