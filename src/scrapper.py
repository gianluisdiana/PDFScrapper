from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
from bs4.element import Tag

from enum import Enum

import re

class Campus(Enum):
    ESIT = 'https://campusingenieriaytecnologia2223.ull.es'

class FirefoxScrapper:
    def __init__(self, options: webdriver.FirefoxOptions, service: Service) -> None:
        self.driver = webdriver.Firefox(service=service, options=options)

    def navigateTo(self, url: str) -> None:
        self.driver.get(url)

    def close(self) -> None:
        self.driver.close()


class ULLScrapper (FirefoxScrapper):
    def __init__(self, profile_path: str, driver_path: str, download_path: str = None, *, verbose: bool = False):
        options = webdriver.FirefoxOptions()
        options.set_preference('profile', profile_path)

        if download_path:
            options.set_preference('browser.download.folderList', 2)
            options.set_preference('browser.download.dir', download_path)
            options.set_preference('browser.download.useDownloadDir', True)

            # Set the application Portable Document Format to only download pdf and not open it
            options.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/pdf')
            options.set_preference('pdfjs.disabled', True)

        super().__init__(options, Service(driver_path))
        self.verbose = verbose

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

        if self.verbose: print(pdf.text[:-5])
        pdf.click()

    def downloadAllPDFs(self) -> None:
        subjects_links = self.getSubjectsLinks()

        for subject_link in subjects_links:
            self.navigateTo(subject_link)
            if self.verbose:
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

            if self.verbose: print()