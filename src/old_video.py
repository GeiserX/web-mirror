import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

options = uc.ChromeOptions()
#options.add_argument('--headless')
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = uc.Chrome(options=options)

url = "https://www.place.holder/VIDEO"
driver.get(url)

# Wait for the page to fully load
time.sleep(5)
video_element = driver.find_element(By.XPATH, "//video[contains(@class, 'vjs-tech')]")
video_src = video_element.get_attribute("src")
video_poster = video_element.get_attribute("poster")
video_filename = "video.mp4"
response = requests.get(video_src)
with open(video_filename, "wb") as f:
    f.write(response.content)

# Save the HTML
html_filename = "webpage_mirror.html"
with open(html_filename, "w", encoding="utf-8") as file:
    file.write(driver.page_source)

# Close the browser
driver.quit()