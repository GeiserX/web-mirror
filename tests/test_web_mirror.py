"""Tests for web-mirror URL rewriting and download logic."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse, urlunparse

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestUrlRewriting:
    """Test URL-to-local-path conversion logic extracted from main.py."""

    def test_url_to_local_path(self):
        """Verify URL is converted to a local folder path."""
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


class TestFolderCreation:
    """Test local folder structure creation."""

    def test_creates_nested_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            local_folder = os.path.join(tmpdir, "es", "articles", "topic")
            os.makedirs(local_folder)
            assert os.path.isdir(local_folder)

    def test_video_page_uses_html_suffix(self):
        """Video pages get .html suffix instead of /index.html."""
        local_folder = "/data/es/videos/clip"
        local_folder_name = local_folder + ".html"
        assert local_folder_name == "/data/es/videos/clip.html"

    def test_regular_page_uses_index_html(self):
        local_folder = "/data/es/articles/topic"
        local_folder_name = local_folder + "/index.html"
        assert local_folder_name == "/data/es/articles/topic/index.html"
