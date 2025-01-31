import datetime
import json
import os
import re
import requests
import shutil
import sys
import time
import uuid
from http.client import IncompleteRead
import logging

from selenium import webdriver
from urllib.request import urlopen

from selenium.common.exceptions import NoSuchElementException

logging.basicConfig(level=logging.INFO, filename='scraper.log')

class Scraper:
    # TODO scrape profile picture
    # TODO scrape other kinds of media
    # TODO scrape journal entries?
    # TODO is the metadata saved?
    # TODO what about when there are no photos to scrape?
    # TODO what about when the user doesn't exist?
    # TODO progress bar
    # TODO when exit the gui, should exit the browser

    def __init__(self):
        self.username = ''
        self.downloadPath = ''
        self.totalPhotos = 0
        self.downloadedPhotos = 0
        self.images = {}
        self.browser = None

    def initBrowser(self, username):
        self.browser = webdriver.Chrome('venv/bin/chromedriver')
        self.browser.set_page_load_timeout(14000)  # did this help? lol

        self.username = username
        logging.info('loading all images')
        self.browser.get('http://vsco.co/' + self.username + '/gallery')

        try:
            button = self.browser.find_element_by_css_selector(
                '#root > div > main > div > div.css-rco518-Container.ebat0h80 > '
                'section > div:nth-child(2) > button')
            button.click()
        except NoSuchElementException:
            logging.info("page not found :(")

        scroll(self.browser, 0.25)
        self.images = self.browser.find_elements_by_class_name('MediaThumbnail ')
        logging.info('finished loading photos')

    def process(self, img):
        url = img.find_element_by_css_selector('a').get_attribute('href')
        mediaId = url[-24:]
        html1 = None

        while True:
            try:
                page = urlopen(url)
                html_bytes = page.read()
                html1 = html_bytes.decode("utf-8")
            except IncompleteRead:
                continue
            else:
                break

        rawJSON = re.findall('window.__PRELOADED_STATE__ = (.*?)</script>', html1)[0]
        data = json.loads(rawJSON).get("medias").get("byId").get(mediaId).get("media")

        self.download("http://" + data.get("responsiveUrl"), data.get("captureDate"))
        self.downloadedPhotos += 1
        sys.stdout.write("\rimages saved: " + str(self.downloadedPhotos) + "/" + str(self.totalPhotos))
        sys.stdout.flush()

    def buildDirectory(self):
        self.downloadPath = self.downloadPath + '/' + self.username

        if not os.path.exists(self.downloadPath):
            logging.info("building folder for " + self.username)
            os.mkdir(self.downloadPath, mode=0o777)
            return

        else:
            i = 1
            while os.path.exists(self.downloadPath + ' (' + str(i) + ')'):
                i += 1
            self.downloadPath = self.downloadPath + ' (' + str(i) + ')'
            os.mkdir(self.downloadPath, mode=0o777)

        logging.info('downloading to ' + self.downloadPath)

    def download(self, url, date):
        if date is None:
            date = str(uuid.uuid1())  # uuid if no capture date information available
        else:
            date = convertDate(date)
        fileName = self.username + ' ' + date + ".jpg"
        r = requests.get(url, stream=True)
        r.raw.decode_content = True
        with open(os.path.join(self.downloadPath, fileName), 'wb') as f:
            shutil.copyfileobj(r.raw, f)


def convertDate(date):
    timestamp = datetime.datetime.fromtimestamp(date / 1000)
    return str(timestamp.strftime('%Y_%m_%d') + ' at ' + timestamp.strftime('%H.%M.%S'))


def scroll(driver, timeout):
    scroll_pause_time = timeout
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height: # If heights are the same, stop
            break
        last_height = new_height
