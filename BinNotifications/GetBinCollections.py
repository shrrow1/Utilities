import datetime
import logging
import os.path
import pickle
import time
from pathlib import Path

from google.auth.transport.requests import Request
# Google Calendar API Imports
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select

from shared_logger import CustomLogger

logger = CustomLogger.CustomLogger(
    name=__name__,
    # log_file="logs/BinCollections.log",
    level=logging.DEBUG
)

class WasteCollectionScraper:
    WAIT_TIMEOUT = 5
    SCOPES = ['https://www.googleapis.com/auth/calendar.events']
    CREDENTIALS_DIR = os.getenv("CREDENTIALS_DIR", "/usr/src/app/Credentials")

    def __init__(self, headless=True):
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument("--headless=new")

        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")

        # Check for system Chromium (Docker paths)
        if os.path.exists("/usr/bin/chromium"):
            self.chrome_options.binary_location = "/usr/bin/chromium"
        elif os.path.exists("/usr/bin/chromium-browser"):
            self.chrome_options.binary_location = "/usr/bin/chromium-browser"

        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.chrome_options.add_argument("--log-level=3")
        self.chrome_options.add_argument("--silent")

        try:
            service = Service(executable_path="/usr/bin/chromedriver")
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
        except Exception:
            self.driver = webdriver.Chrome(options=self.chrome_options)

        self.wait = WebDriverWait(self.driver, 15)

    def find_collection_dates(self, url, postcode, address_substring):
        try:
            logger.info(f"Navigating to {url}...")
            self.driver.get(url)
            try:
                cookie_accept_button = WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                    EC.element_to_be_clickable((By.ID, 'newConsentGranted'))
                )
                cookie_accept_button.click()
            except (TimeoutException, NoSuchElementException):
                pass

            postcode_input = self.wait.until(EC.visibility_of_element_located((By.ID, "txtBxPCode")))
            postcode_input.clear()
            postcode_input.send_keys(postcode)
            self.driver.find_element(By.ID, "btnFindAddr").click()

            address_dropdown_element = self.wait.until(EC.visibility_of_element_located((By.ID, "lstBxAddrList")))
            dropdown = Select(address_dropdown_element)

            found = False
            for option in dropdown.options:
                if address_substring.lower() in option.text.lower():
                    dropdown.select_by_visible_text(option.text)
                    logger.info(f"Selected address: {option.text}")
                    found = True
                    break

            if not found:
                logger.error("Address not found in dropdown.")
                return None

            time.sleep(1)
            self.driver.find_element(By.ID, "MainContent_btnGetSchedules").click()
            self.wait.until(EC.presence_of_element_located((By.ID, "lblSelectedAddr")))

            results = {}
            bin_headers = self.driver.find_elements(By.XPATH, "//strong[contains(translate(text(), 'BIN', 'bin'), 'bin')]")

            for header in bin_headers:
                try:
                    bin_type = header.text.strip()
                    parent = header.find_element(By.XPATH, "./ancestor::div[contains(@style, 'margin:5px')][1]")
                    date_element = parent.find_element(By.XPATH, ".//div[contains(text(), 'Next collection on:')]/following-sibling::div")
                    raw_date = date_element.text.strip()
                    bin_date = raw_date.split(', ')[1] if ',' in raw_date else raw_date

                    if bin_date in results:
                        results[bin_date] = f"{results[bin_date]} & {bin_type}"
                    else:
                        results[bin_date] = bin_type
                except (NoSuchElementException, IndexError):
                    continue
            return results
        finally:
            self.driver.quit()

    def sync_to_google_calendar(self, data):

        pickle_file =Path(f'{self.CREDENTIALS_DIR}/token.pickle')
        credentials_file =Path(f'{self.CREDENTIALS_DIR}/credentials.json')

        if not data:
            return

        creds = None
        # Load existing credentials if token.pickle exists and is non-empty
        if os.path.exists(pickle_file) and os.path.getsize(pickle_file) > 0:
            with open(pickle_file, 'rb') as token:
                creds = pickle.load(token)

        # Handle headless OAuth setup safely without locking Docker logs
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials...")
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.info(f"Failed to refresh token: {e}. Re-authorization required.")
                    creds = None

            if not creds:
                if not os.path.exists(credentials_file):
                    logger.error(f"Error: Google Credentials file not found at {credentials_file}")
                    return

                # Prevent the script from hanging indefinitely during an unattended automation/cron run
                is_interactive = os.environ.get("INTERACTIVE_AUTH", "false").lower() == "true"
                if not is_interactive:
                    logger.error("\n[ERROR] No valid Google API credentials or active session found.")
                    logger.error("Please run this script once locally in interactive mode to generate 'token.pickle',")
                    logger.error(f"then copy 'token.pickle' into your Docker container's directory: {self.CREDENTIALS_DIR}")
                    logger.error("To force manual link authorization, set the environment variable INTERACTIVE_AUTH=true")
                    return

                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, self.SCOPES)

                try:
                    # Attempt local server authentication first
                    creds = flow.run_local_server(port=0)
                except Exception as server_error:
                    # OOB Console fxallback (requires manual input)
                    logger.error("\n*** ACTION REQUIRED ***")
                    logger.error("Could not open local browser window. Please use this authorization URL:")
                    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
                    logger.error(f"\n{auth_url}\n")

                    try:
                        # Add an input timeout safety if needed or wait for user input
                        code = input("Enter the authorization code: ").strip()
                        flow.fetch_token(code=code)
                        creds = flow.credentials
                    except Exception as token_error:
                        logger.error(f"Error retrieving authentication token: {token_error}")
                        return

            # Save token for next run to prevent authorization flows in the future
            if creds:
                with open(pickle_file, 'wb') as token:
                    pickle.dump(creds, token)
                    logger.info(f"Token saved successfully to {pickle_file}")

        if not creds:
            logger.error("Authentication failed. Aborting calendar synchronization.")
            return

        service = build('calendar', 'v3', credentials=creds)

        for date_str, bin_info in data.items():
            try:
                date_obj = datetime.datetime.strptime(date_str, "%d %b %Y")
                iso_start = date_obj.strftime("%Y-%m-%d")
                iso_end = (date_obj + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                summary = f'Bins: {bin_info}'

                events_result = service.events().list(
                    calendarId='primary',
                    timeMin=f"{iso_start}T00:00:00Z",
                    timeMax=f"{iso_start}T23:59:59Z",
                    singleEvents=True
                ).execute()

                if any(event.get('summary') == summary for event in events_result.get('items', [])):
                    logger.info(f"Skipping duplicate: {iso_start}")
                    continue

                event = {
                    'summary': summary,
                    'description': f'Automated reminder: {bin_info}',
                    'start': {'date': iso_start},
                    'end': {'date': iso_end},
                    'reminders': {'useDefault': False, 'overrides': [{'method': 'email', 'minutes': 24 * 60}]}
                }
                service.events().insert(calendarId='primary', body=event).execute()
                logger.info(f"Synced: {iso_start}")
            except Exception as e:
                logger.error(f"Error syncing {date_str}: {e}")

def get_config():
    config = {}
    config["url"] = os.environ.get("COLLECTIONS_URL", "https://webapps.dacorum.gov.uk/bincollections")
    config["postcode"] = os.environ.get("POSTCODE", "")
    config["address"] = os.environ.get("ADDRESS_SEARCH", "")
    return config

if __name__ == "__main__":
    CONFIG = get_config()
    logger.info("Starting")
    if not CONFIG["postcode"] or not CONFIG["address"]:
        logger.error("Please configure environment variables POSTCODE and ADDRESS_SEARCH.")
    else:
        scraper = WasteCollectionScraper(headless=True)
        data = scraper.find_collection_dates(CONFIG["url"], CONFIG["postcode"], CONFIG["address"])
        if data:
            scraper.sync_to_google_calendar(data)