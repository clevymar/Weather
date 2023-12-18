# %%
import time
import datetime
import sys, os
from os import path
from collections import namedtuple
import traceback

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from scrapping import send_email, start_driver


# %%
# CHROMEDRIVER_PATH = r"C:\Program Files\chromedriver.exe"
URL_ROOT = "https://snow.myswitzerland.com/snow_reports/"
SnowConditions = namedtuple("SnowConditions", "snowLevel snowinResort snowQuality snowLastFall openLifts")

stations = {
    "Andermatt": "andermatt-oberalp-sedrun-111",
    "Engelberg": "engelberg-titlis-73",
    "Hoch-Ybrig": "och-ybrig-26",
    "Wengen": "wengen-jungfrau-ski-region-91",
    "Laax": "flims-laax-falera-67",
    "Verbier": "verbier-132",
}

COOKIE_ID = "onetrust-accept-btn-handler"
BUTTON_XPATH = "/html/body/div[1]/div[1]/div[2]/div/div/div[1]/div[5]/div[2]/div/div[1]/div/article[1]/div/div/div[1]/button"


# %%
def return_info(driver):
    dRes = {}

    try:
        TABLE_XPATH = "/html/body/div[1]/div[1]/div[2]/div/div/div[1]/div[5]/div[2]/div/div[1]/div/article[1]/div/div/div[2]/div/div[3]/table/tbody"
        details = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, TABLE_XPATH)))
        rows = details.find_elements(By.TAG_NAME, "tr")
        dRes["Snow depth"] = [rows[0].text, rows[1].text, rows[-1].text]
    except TimeoutException:
        print(f"[-] Timeout getting table")
    except Exception as e:
        print(f"[-] Error processing: {e}")
        print(traceback.format_exc())

    elSnowForecast = driver.find_element(By.CSS_SELECTOR, "ul.SnowChart")
    links = elSnowForecast.find_elements(By.TAG_NAME, "li")
    for i, l in enumerate(links):
        snowFall = l.get_attribute("data-title")
        tmp = {"snowfall": snowFall}
        dRes["day" + str(i)] = tmp

    elements = driver.find_elements(By.CSS_SELECTOR, "li.QuickFacts--value")
    content = [el.text for el in elements if len(el.text.strip()) > 0]
    for i in range(7):
        dRes["day" + str(i)]["Temperature"] = content[i]
    snowLevel = content[7]
    snowQuality = content[8]
    snowLastFall = content[9]
    openLifts = content[-1]

    elements = driver.find_elements(By.CSS_SELECTOR, "li.QuickFacts--content")
    content = [el.text for el in elements if len(el.text.strip()) > 0]
    for i in range(7):
        dRes["day" + str(i)]["Conditions"] = content[i]
    snowinResort = content[10].split(" in")[0]
    snowConditions = SnowConditions(snowLevel, snowinResort, snowQuality, snowLastFall, openLifts)
    dRes["snow conditions"] = snowConditions

    return dRes


# %%
def text_body(dictAll):
    body = ""
    for key, item in dictAll.items():
        # print(f"\n\n**********   {key}")
        body += f"\n\n**********   {key}\n"
        snowCond = item["snow conditions"]
        to_print = [f"{name}: {getattr(snowCond, name)}" for name in snowCond._fields]
        body += f"Snow conditions: {'; '.join(to_print)}" + "\n"
        if "Snow depth" in item.keys() and len(sd := item["Snow depth"]) > 0:
            to_print = [c[14:] if c.startswith("Depth of snow") else c for c in sd]
            body += f"Snow depth: {'; '.join(to_print)}" + "\n"
        for i in range(7):
            d = item["day" + str(i)]
            label = d["snowfall"].split()[0]
            body += (
                f'Forecast for {label} {d["Conditions"]:<20} - {d["Temperature"]} - expected snowfall {" ".join(d["snowfall"].split()[1:])}' + "\n"
            )

    return body


def html_body(dictAll):
    html = """\
        <html>
        <head></head>
        <body>
        """
    for key, item in dictAll.items():
        html += f"\n\n<h2>{key}</h2>\n"
        snowCond = item["snow conditions"]
        to_print = [f'{name}: <span style="color: red;">{getattr(snowCond, name)} </span>' for name in snowCond._fields]
        html += f"<p><b>Snow conditions:</b> {'; '.join(to_print)}</p>"
        if "Snow depth" in item.keys() and len(sd := item["Snow depth"]) > 0:
            to_print = [c[14:] if c.startswith("Depth of snow") else c for c in sd]
            html += f"<b>Snow depth:</b> {'; '.join(to_print)}</p>"

        html += "<font color='black'><h3>Forecast for </h3><ul>"
        for i in range(7):
            d = item["day" + str(i)]
            label = d["snowfall"].split()[0]
            html += f'<li><pre><b>{label}</b> {d["Conditions"]:<26} - {d["Temperature"]} '
            html += f'- expected snowfall {" ".join(d["snowfall"].split()[1:])}</pre></li>'
        html += "</ul>"

    html += """
        </body>
        </html>
        """
    return html


if __name__ == "__main__":
    # service = Service(executable_path=CHROMEDRIVER_PATH)
    # driver = webdriver.Chrome(service=service)
    driver = start_driver(forCME=True)
    hasCookieBeenClicked = False
    # driver.maximize_window()
    dictAll = {}
    try:
        for station, url_end in stations.items():
            t0 = time.perf_counter()
            print(f"Processing for {station}")
            url = URL_ROOT + url_end + "/"
            try:
                driver.get(url)
                # get rid of cookies
                if not hasCookieBeenClicked:
                    cookieButton = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, COOKIE_ID)))
                    if cookieButton:
                        cookieButton.click()
                        print("Cookie button clicked")
                        hasCookieBeenClicked = True
                # driver.execute_script("window.scrollTo(100,document.body.scrollHeight);")
                accordion = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, BUTTON_XPATH)))
                driver.execute_script("arguments[0].scrollIntoView();", accordion)
                accordion.click()
                if accordion.get_attribute("aria-expanded") == "false":
                    accordion.click()
                time.sleep(1)
                dictAll[station] = return_info(driver)
                print(f"[+]{station} processed in {time.perf_counter()-t0:.0f} seconds")
            except TimeoutException:
                print(f"[-] Timeout getting accordion button for {station}")
            except Exception as e:
                print(f"[-] Error processing {station}: {e}")
                print(traceback.format_exc())
    finally:
        driver.quit()
    body = html_body(dictAll)
    # display(HTML(body))
    send_email("Ski resorts condition - " + datetime.datetime.today().strftime("%A %d %B"), body)
