import os
from bs4 import BeautifulSoup
import requests
import requests_cache
from urllib.parse import urlparse, urlunparse
import time
import shutil
import logging
import sys
from playwright.sync_api import sync_playwright

# destlocationdir = "/data/"
language = "es"
fulldir = "/data/" # + language

logger = logging.getLogger('mylogger')
logger.setLevel(logging.INFO)  # set logger level
logFormatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
consoleHandler = logging.StreamHandler(sys.stdout)  # set streamhandler to stdout
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)


def get_sitemap():
    requests_cache.install_cache(fulldir + '/sitemap')
    session = requests_cache.CachedSession('sitemap', expire_after=86400)  # 24h
    web = "https://www.place.holder/"
    links = []
    r = requests.get(web + language + "/sitemap.xml")
    soup = BeautifulSoup(r.text, "lxml")
    url_locs = soup.find_all("loc")
    for url in url_locs:
        links.append(url.text)
    return ["https://www.place.holder/VIDEO"]
    # return links


def download_video(url, filename):
    with requests.get(url, stream=True) as r:
        with open(filename, "wb") as f:
            shutil.copyfileobj(r.raw, f)


def download_webpage(url, context):
    page = context.new_page()
    page.goto(url)
    local_url = urlparse(url)._replace(netloc="", scheme="")
    local_folder = fulldir + urlunparse(local_url)
    if not os.path.exists(local_folder):
        os.makedirs(local_folder)
    time.sleep(3)
    page_content = page.content()
    bs_page = BeautifulSoup(page_content, "html.parser")

    # video page
    video = bs_page.find("video")
    if video:
        video_url = video["src"]
        video_filename = os.path.basename(urlparse(video_url).path)
        local_video_path = local_folder + "/" + video_filename
        print(local_video_path)
        download_video(video_url, local_video_path)
        video["src"] = "/" + local_video_path
        local_folder_name = local_folder + ".html"  # If it's a video, do not add /index.html
    else:
        local_folder_name = local_folder + "/index.html"

    # href modification
    for tag_name, attribute_name in [("a", "href"), ("link", "href"), ("base", "href")]:
        for tag in bs_page.find_all(tag_name, **{attribute_name: True}):
            if tag[attribute_name].startswith("https://www.place.holder/"):
                tag[attribute_name] = tag[attribute_name].replace("https://www.place.holder", "")

    with open(local_folder_name, "w", encoding="utf-8") as file:
        file.write(str(bs_page))


if __name__ == '__main__':
    if not os.path.exists(fulldir):
        os.makedirs(fulldir)
    links = get_sitemap()
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(extra_http_headers=headers)
        for link in links:
            logger.info(link)
            download_webpage(link, context)
        browser.close()

