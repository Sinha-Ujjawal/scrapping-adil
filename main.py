import time
import os
import logging
from typing import List, Tuple

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__file__)


ADIL_WEBPAGE = "https://www.douane.gov.ma/adil/"
SAVE_INTO = "./data"
SLEEP_TIME = 5  # seconds
TIMEOUT = 60 # seconds


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
    return list(map(lambda opt: opt.get_attribute("title") or opt.text, select.options[1:]))


def main():
    logger.info(f"Srapping data from page: {ADIL_WEBPAGE}")
    os.makedirs(SAVE_INTO, exist_ok=True)
    # Set Chrome options
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    with webdriver.Chrome(options=options) as driver:
        driver.get(ADIL_WEBPAGE); my_sleep(SLEEP_TIME)
        WebDriverWait(driver, TIMEOUT).until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "principal")))
        chapters = chapters_from_homepage(driver)
        df_chapters = pd.DataFrame(list(enumerate(chapters, 1)), columns=["chapter_id", "chapter"])
        chapters_file_path = f"{SAVE_INTO}/chapters.csv"
        logger.info(f"Saving chapters title into: `{chapters_file_path}`")
        df_chapters.to_csv(chapters_file_path, index=False)
        for idx, chapter in enumerate(chapters, 1):
            logger.info(f"Scrapping data for chapter_{idx}: `{chapter}`")
            select, submit_button = select_and_submit_from_homepage(driver)
            select.select_by_index(idx)
            submit_button.click(); my_sleep(SLEEP_TIME)
            try:
                WebDriverWait(driver, TIMEOUT).until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "mainFrame")))
                logger.info("Collecting data...")
                data = []
                table = driver.find_element(By.TAG_NAME, "table")
                for row in table.find_elements(By.TAG_NAME, "tr"):
                    cells = row.find_elements(By.TAG_NAME, "td")
                    data.append([cell.text for cell in cells])
                data_df = pd.DataFrame(data)
                file = f"{SAVE_INTO}/chapter_{idx}.csv"
                logger.info(f"Saving data to `{file}`")
                data_df.to_csv(file, index=False)
            except TimeoutException as e:
                logger.error(f"Error occurred: {e}")
                logger.info("Seems like the mainFrame is not found in the page. Skipping to the next chapter")
            driver.back(); my_sleep(SLEEP_TIME)
            WebDriverWait(driver, TIMEOUT).until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "principal")))
    logger.info("All data scraped.")


if __name__ == "__main__":
    main()

