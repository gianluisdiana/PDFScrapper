from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
from bs4.element import Tag

import os
import re
import time
from enum import Enum, auto

from options import Options
from functions import formatText, getOldestFile

class Campus(Enum):
    ESIT = 'https://campusingenieriaytecnologia2223.ull.es'
    ESIT2122 = 'https://campusingenieriaytecnologia2122.ull.es'

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
        self.downloaded_files: list[dict] = []
        self.pdf_downloaded = 0

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

    def getSectionResources(self, section: Tag) -> list[Tag]:
        return [
            *section.find_all('li', 'activity resource modtype_resource'),
            *section.find_all('li', 'activity resource modtype_resource hasinfo'),
            *section.find_all('li', 'activity url modtype_url'),
            *section.find_all('li', 'activity url modtype_url hasinfo'),]

    def downloadPDF(self, resource: Tag) -> str:
        pdf = self.driver.find_element(By.ID, resource.get('id')) \
            .find_element(By.CLASS_NAME, 'aalink')

        # Not interested in non-pdf files.
        if 'pdf' not in pdf.find_element(By.TAG_NAME, 'img').get_attribute('src'): return

        pdf_name = " ".join(re.findall(r'\w+', pdf.text)[:-1])
        if self.options.verbose: print(f'   - {pdf_name}')
        pdf.click()

        # Wait for the file to be downloaded, checking the amount of files in the folder.
        while self.pdf_downloaded == len(os.listdir(self.options.download_path)):
            time.sleep(0.1)

        self.pdf_downloaded += 1

        return pdf_name

    def downloadAllPDFs(self) -> None:
        subjects_links = self.getSubjectsLinks()

        for subject_link in subjects_links:
            self.navigateTo(subject_link)

            subject_name = formatText(self.driver.title.split(": ")[1])
            subject_path = os.path.join(self.options.download_path, subject_name)
            if self.options.verbose: print(subject_name)

            course_sections = self.getCourseContent().find_all('li', 'section main clearfix')

            for section in course_sections:
                section_title = ' '.join(re.findall(r'[-\w]+', section.find('h3', 'sectionname').text))
                section_path = os.path.join(subject_path, section_title)
                if self.options.verbose: print(f' - {section_title}')

                for resource in self.getSectionResources(section):
                    pdf_name = self.downloadPDF(resource)

                    if pdf_name is None: continue
                    self.downloaded_files.append({'name': pdf_name, 'path': section_path})

                    # Keep the browser on the same subject page.
                    if self.driver.current_url != subject_link: self.navigateTo(subject_link)

            if self.options.verbose: print()

    def renameDownloadedFiles(self) -> None:
        for file in self.downloaded_files:
            new_path = os.path.join(file['path'], file['name'] + '.pdf')
            downloaded_file = getOldestFile(self.options.download_path, '.pdf')
            os.renames(downloaded_file, new_path)
