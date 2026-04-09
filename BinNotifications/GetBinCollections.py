import time
from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
import json

class WasteCollectionScraper:
    WAIT_TIMEOUT = 5

    def __init__(self, headless=True):
        """
        Initializes the Selenium WebDriver with headless mode and suppressed logging.
        """
        self.chrome_options = Options()

        # 1. SUPPRESS VISIBLE WINDOW (Headless mode)
        if headless:
            self.chrome_options.add_argument("--headless=new")

        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--window-size=1920,1080")

        # 2. SUPPRESS CONSOLE ERRORS
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.chrome_options.add_argument("--log-level=3")  # Fatal errors only
        self.chrome_options.add_argument("--silent")

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
                pass

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
            self.wait.until(EC.presence_of_element_located((By.ID, "lblSelectedAddr")))

            print("Scraping results...")
            results = {}

            # Strategy: Find all strong tags that contain 'bin'
            bin_headers = self.driver.find_elements(By.XPATH,
                                                    "//strong[contains(translate(text(), 'BIN', 'bin'), 'bin')]")

            for header in bin_headers:
                try:
                    bin_type = header.text.strip()
                    # Traverse up to the margin:5px div container then find the date cell
                    parent_container = header.find_element(By.XPATH,
                                                           "./ancestor::div[contains(@style, 'margin:5px')][1]")
                    date_element = parent_container.find_element(By.XPATH,
                                                                 ".//div[contains(text(), 'Next collection on:')]/following-sibling::div")

                    bin_date = date_element.text.strip()[5:]
                    # results[bin_type] = bin_date
                    if bin_date in results:
                        results[bin_date] = f'{results[bin_date]}, {bin_type}'
                    else:
                        results[bin_date] = bin_type
                    print(f"Found: {bin_date} -> {bin_type}")
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

    scraper = WasteCollectionScraper(headless=True)
    data = scraper.find_collection_dates(TARGET_URL, MY_POSTCODE, MY_HOUSE)

    if data:
        print("\n--- Final Collection Schedule ---")
        for bin_name, bin_date in data.items():
            print(f"{bin_name}: {bin_date}")
    else:
        print("No data retrieved.")