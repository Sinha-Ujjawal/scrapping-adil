import time
import logging
from typing import List, Tuple

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


ADIL_WEBPAGE = "https://www.douane.gov.ma/adil/"


def my_sleep(secs: int):
    logger.info(f"Sleeping for {secs} seconds")
    time.sleep(secs)


def select_and_submit_from_homepage(driver: webdriver.Chrome) -> Tuple[Select, WebElement]:
    select_element = driver.find_element(By.NAME, "Recherche1")
    submit_button = select_element.find_element(By.XPATH, "./following-sibling::input[@value='Trouver...']")
    select = Select(select_element)
    options = select.options
    return select, submit_button


def chapters_from_homepage(driver: webdriver.Chrome) -> List[str]:
    select, submit_button = select_and_submit_from_homepage(driver)
    return list(map(lambda opt: opt.text, select.options[1:]))


def main():
    logger.info(f"Srapping data from page: {ADIL_WEBPAGE}")
    # Set Chrome options
    options = Options()
    with webdriver.Chrome(options=options) as driver:
        driver.get(ADIL_WEBPAGE); my_sleep(10)
        driver.switch_to.frame("principal")
        chapters = chapters_from_homepage(driver)

        for idx, chapter in enumerate(chapters, 1):
            logger.info(f"Scrapping data for {chapter}")
            select, submit_button = select_and_submit_from_homepage(driver)
            select.select_by_index(idx)
            submit_button.click(); my_sleep(10)
            try:
                driver.find_elements(By.NAME, "mainFrame")
                driver.switch_to.frame("mainFrame")
                logger.info("Collecting data...")
                data = []
                table = driver.find_element(By.TAG_NAME, "table")
                for row in table.find_elements(By.TAG_NAME, "tr"):
                    cells = row.find_elements(By.TAG_NAME, "td")
                    data.append([cell.text for cell in cells])
                data_df = pd.DataFrame(data)
                file = f"./{chapter}.csv"
                logger.info(f"Saving data to {file}")
                data_df.to_csv(file, index=False)
            except Exception as err:
                logger.error(f"Error occurred: {err}")
                logger.info("Going to the next chapter")
            driver.back(); my_sleep(10)
            driver.switch_to.frame("principal")
    logger.info("All data scraped.")


if __name__ == "__main__":
    main()

