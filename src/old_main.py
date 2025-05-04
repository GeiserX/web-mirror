import os
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
#from selenium import webdriver
import undetected_chromedriver as uc

def extract_links(driver, visited_links):
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    new_links = set()
    for link in soup.find_all('a', href=True):
        parsed_url = urljoin(driver.current_url, link['href'])
        if link['href'].startswith("/" + language) and parsed_url not in visited_links:
            new_links.add(parsed_url)
    return new_links

def recursive_crawl(driver, url, visited_links):
    visited_links.add(url)
    driver.get(url)
    local_url = urlparse(url)._replace(netloc="", scheme="")
    local_folder = urlunparse(local_url).removeprefix("/")

    if not os.path.exists(local_folder):
        os.makedirs(local_folder)
    
    with open(local_folder + "index.html", "w", encoding="utf-8") as file:
        file.write(driver.page_source)
    
    new_links = extract_links(driver, visited_links)

    for new_link in new_links:
        if new_link not in visited_links:
            recursive_crawl(driver, new_link, visited_links)


if __name__ == '__main__':
    base_url = 'https://www.place.holder/'
    language = "es"
    url = base_url + language

    options = uc.ChromeOptions()
    #options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    visited_links = set()
    with uc.Chrome(options=options) as driver:
        recursive_crawl(driver, url, visited_links)