import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException


class WasteCollectionScraper:
    WAIT_TIMEOUT = 5

    def __init__(self, headless=False):
        """
        Initializes the Selenium WebDriver with optional headless mode.
        """
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.wait = WebDriverWait(self.driver, 15)

    def find_collection_dates(self, url, postcode, address_substring):
        """
        Specific workflow for Dacorum Borough Council waste lookup using XPath.
        """
        try:
            print(f"Navigating to {url}...")
            self.driver.get(url)

            # 1. Handle Cookie Consent
            try:
                cookie_accept_button = WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                    EC.element_to_be_clickable((By.ID, 'newConsentGranted'))
                )
                cookie_accept_button.click()
                print("Cookies accepted.")
            except (TimeoutException, NoSuchElementException):
                print("Cookie banner not found or already dismissed.")

            # 2. Find and fill the postcode input
            print(f"Entering postcode: {postcode}")
            postcode_input = self.wait.until(EC.visibility_of_element_located((By.ID, "txtBxPCode")))
            postcode_input.clear()
            postcode_input.send_keys(postcode)

            # Click the 'Find Address' button
            find_address_btn = self.driver.find_element(By.ID, "btnFindAddr")
            find_address_btn.click()

            # 3. Wait for the address dropdown
            print("Waiting for address results...")
            address_dropdown_element = self.wait.until(EC.visibility_of_element_located((By.ID, "lstBxAddrList")))

            # 4. Select the specific address
            dropdown = Select(address_dropdown_element)
            found = False
            for option in dropdown.options:
                if address_substring.lower() in option.text.lower():
                    dropdown.select_by_visible_text(option.text)
                    print(f"Selected address: {option.text}")
                    found = True
                    break

            if not found:
                print(f"Could not find address containing '{address_substring}' in the list.")
                return None

            # 5. Submit to get collection dates
            time.sleep(1)
            submit_btn = self.driver.find_element(By.ID, "MainContent_btnGetSchedules")
            submit_btn.click()

            # 6. Scrape the results using XPath
            # We wait for the specific text that indicates the schedule has loaded
            # self.wait.until(
            #     EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'collection schedule for')]")))
            self.wait.until(EC.presence_of_element_located((By.ID, "lblSelectedAddr")))

            print("Scraping results with XPath...")
            results = {}

            # Strategy: Find all strong tags that contain 'bin'
            # Then find the relative date container
            bin_headers = self.driver.find_elements(By.XPATH,
                                                    "//strong[contains(translate(text(), 'BIN', 'bin'), 'bin')]")

            for header in bin_headers:
                try:
                    bin_type = header.text.strip()

                    # Based on your HTML, the date is in a div with display:table-cell
                    # following the bin name. We look for the next div that contains a date-like string.
                    # XPath: Go up to the container div, then find the cell with the date text
                    parent_container = header.find_element(By.XPATH,
                                                           "./ancestor::div[contains(@style, 'margin:5px')][1]")
                    date_element = parent_container.find_element(By.XPATH,
                                                                 ".//div[contains(text(), 'Next collection on:')]/following-sibling::div")

                    bin_date = date_element.text.strip()
                    results[bin_type] = bin_date
                    print(f"Found: {bin_type} -> {bin_date}")
                except NoSuchElementException:
                    continue

            return results

        except TimeoutException:
            print("Error: The page took too long to load or results didn't appear.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            print("Closing browser...")
            self.driver.quit()


if __name__ == "__main__":
    # CONFIGURATION
    TARGET_URL = "https://webapps.dacorum.gov.uk/bincollections"
    MY_POSTCODE = "HP4 3TH"
    MY_HOUSE = "8 Boswick Lane"

    scraper = WasteCollectionScraper(headless=False)
    data = scraper.find_collection_dates(TARGET_URL, MY_POSTCODE, MY_HOUSE)

    if data:
        print("\n--- Final Collection Schedule ---")
        for bin_name, bin_date in data.items():
            print(f"{bin_name}: {bin_date}")
    else:
        print("No data retrieved.")