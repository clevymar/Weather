import sys, os
from os import path


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

if os.environ.get("HOMEPATH") == "\\Users\\clevy":
    LOCATION = "LOCAL"
else:
    LOCATION = "SERVER"


def isLocal():
    return LOCATION == "LOCAL"


if isLocal():
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    sys.path.append(os.path.realpath("."))
    sys.path.append("C:/Users/clevy/OneDrive/Python Scripts/CLM_utils")
else:
    sys.path.append("/home/CyrilFinanceData/FinDataScrap/utils")

from email_CLM import send_email


class SeleniumError(Exception):
    pass


def start_driver(headless=True, forCME=False, webGL=True):
    """
    The function `start_driver` creates a headless Chrome driver with specific options"""

    try:
        driver = None
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        if webGL:
            chrome_options.add_argument("--enable-unsafe-swiftshader")
        if forCME:
            chrome_options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36"
            )
            chrome_options.add_argument("--window-size=1920,1080")
            # chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--headless=new")

        else:
            if headless:
                chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--log-level=3")
        driver = webdriver.Chrome(options=chrome_options)

        return driver
    except Exception as e:
        if driver:
            driver.quit()
        raise Exception("Could not create the driver") from e


def selenium_scrap_simple(link: str):
    """
    The function `selenium_scrap_simple` uses Selenium to scrape the HTML source code of a given link.
    :param link: The `link` parameter is a string that represents the URL of the webpage you want to
    scrape using Selenium
    """
    html_source = None
    driver = start_driver()
    try:
        driver.get(link)
        html_source = driver.page_source
    except Exception as e:
        raise Exception("Could not scrap the link at {link}") from e
    finally:
        print("Quitting Selenium driver")
        driver.quit()
    return html_source
