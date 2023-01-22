from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
from bs4.element import Tag
from enum import Enum, auto
from options import Options

import re

class Campus(Enum):
    ESIT = 'https://campusingenieriaytecnologia2223.ull.es'

class Browser(Enum):
    SAFARI = auto()
    FIREFOX = auto()

class Scrapper:
    """Represents a basic browser scrapper.

    Attributes:
        driver (webdriver):
            The webdriver to use.
        options (Options):
            The options to configure the scrapper."""

    def __init__(self, browser: Browser, options: Options = None) -> None:
        """Initializes the scrapper. If no options are provided, the default options will be used.

        Args:
            browser (Browser): An enum with the browser to use.
            options (Options): The options to configure the scrapper."""
        self.options = options if options is not None else Options()

        if browser == Browser.SAFARI:
            self.driver = webdriver.Safari()
        elif browser == Browser.FIREFOX:
            if options is None:
                raise ValueError('Firefox webdriver needs to know the driver path and profile path')

            if options.profile_path is None:
                raise ValueError('Profile path not provided')

            firefox_options = webdriver.FirefoxOptions()
            firefox_options.set_preference('profile', options.profile_path)

            if options.download_path:
                firefox_options.set_preference('browser.download.folderList', 2)
                firefox_options.set_preference('browser.download.dir', options.download_path)
                firefox_options.set_preference('browser.download.useDownloadDir', True)

                # Set the application Portable Document Format to only download pdf and not open it
                firefox_options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/pdf')
                firefox_options.set_preference('pdfjs.disabled', True)

            if options.driver_path is None:
                raise ValueError('Driver path not provided')

            self.driver = webdriver.Firefox(service=Service(options.driver_path), options=firefox_options)

    def navigateTo(self, url: str) -> None:
        """Navigates to the given URL.

        Args:
            url (str): The URL to browse to."""
        self.driver.get(url)

    def close(self) -> None:
        """Closes the browser."""
        self.driver.close()


class ULLScrapper (Scrapper):
    def __init__(self, browser: Browser, options: Options = None) -> None:
        super().__init__(browser, options)

    def goToLogin(self) -> None:
        WebDriverWait(self.driver, 5) \
            .until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.btn-primary.btn-block"))) \
            .click()

    def login(self, username: str, password: str) -> None:
        WebDriverWait(self.driver, 5) \
            .until(EC.element_to_be_clickable((By.ID, "username"))) \
            .send_keys(username)

        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.NAME, "submit").click()

    def loginCampus(self, campus: Campus, username: str, password: str) -> None:
        self.navigateTo(campus.value)
        self.goToLogin()
        self.login(username, password)

    def getSubjectsLinks(self) -> list[str]:
        course_list = WebDriverWait(self.driver, 5) \
            .until(EC.presence_of_element_located((By.CLASS_NAME, "course_list")))

        course_list = BeautifulSoup(course_list.get_attribute('innerHTML'), 'html.parser')
        return [link.get('href') for link in course_list.find_all('a')]

    def getCourseContent(self) -> BeautifulSoup:
        course_content = WebDriverWait(self.driver, 5) \
            .until(EC.presence_of_element_located((By.CLASS_NAME, "course-content")))
        return BeautifulSoup(course_content.get_attribute('innerHTML'), 'html.parser')

    def downloadPDF(self, resource: Tag) -> None:
        pdf = self.driver.find_element(By.ID, resource.get('id')) \
            .find_element(By.CLASS_NAME, 'aalink')

        # Not interested in non-pdf files.
        if 'pdf' not in pdf.find_element(By.TAG_NAME, 'img').get_attribute('src'): return

        if self.options.verbose: print(f' - {pdf.text[:-5]}')
        # pdf.click()

    def downloadAllPDFs(self) -> None:
        subjects_links = self.getSubjectsLinks()

        for subject_link in subjects_links:
            self.navigateTo(subject_link)
            if self.options.verbose:
                subject_name = " ".join(re.findall(r'\w+', self.driver.title[8:])).title().replace(" ", "")
                print(subject_name)

            course_content = self.getCourseContent()
            course_resources = [
                *course_content.find_all('li', 'activity resource modtype_resource'),
                *course_content.find_all('li', 'activity resource modtype_resource hasinfo'),
                *course_content.find_all('li', 'activity url modtype_url'),
                *course_content.find_all('li', 'activity url modtype_url hasinfo'),]

            for resource in course_resources:
                self.downloadPDF(resource)

            if self.options.verbose: print()