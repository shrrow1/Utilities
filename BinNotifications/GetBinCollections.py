import time
import datetime
import os.path
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Google Calendar API Imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import time
import os
from pathlib import Path

class WasteCollectionScraper:
    WAIT_TIMEOUT = 5
    SCOPES = ['https://www.googleapis.com/auth/calendar.events']
    CREDENTIALS_DIR = "/usr/src/app/Credentials"

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
            print(f"Navigating to {url}...")
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
                    print(f"Selected address: {option.text}")
                    found = True
                    break

            if not found:
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
        # Load the existing token if it exists
        if os.path.exists(pickle_file) and os.path.getsize(pickle_file) > 0:
            with open(pickle_file, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_file):
                    print("Error: 'credentials.json' not found.")
                    return

                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, self.SCOPES)

                try:
                    # Attempt local server first (works on desktop)
                    creds = flow.run_local_server(port=0)
                except Exception:
                    # Fallback for Docker/Headless
                    print("\n*** ACTION REQUIRED ***")
                    print("Could not open browser. Please use the following link to authorize the app:")
                    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
                    print(f"\n{auth_url}\n")
                    code = input("Enter the authorization code: ").strip()
                    flow.fetch_token(code=code)
                    creds = flow.credentials

            # Save the credentials for the next run (including the refresh token)
            with open(pickle_file, 'wb') as token:
                pickle.dump(creds, token)
                print("Token saved/refreshed to token.pickle")

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
                    print(f"Skipping duplicate: {iso_start}")
                    continue

                event = {
                    'summary': summary,
                    'description': f'Automated reminder: {bin_info}',
                    'start': {'date': iso_start},
                    'end': {'date': iso_end},
                    'reminders': {'useDefault': False, 'overrides': [{'method': 'email', 'minutes': 24 * 60}]}
                }
                service.events().insert(calendarId='primary', body=event).execute()
                print(f"Synced: {iso_start}")
            except Exception as e:
                print(f"Error syncing {date_str}: {e}")

def get_config():
    config={}
    config["url"] = os.environ["COLLECTIONS_URL"]
    config["postcode"] = os.environ["POSTCODE"]
    config["address"] = os.environ["ADDRESS_SEARCH"]
    return config

if __name__ == "__main__":
    CONFIG = get_config()
    # CONFIG = {"url": "https://webapps.dacorum.gov.uk/bincollections", "pc": "HP4 3TH", "addr": "8 Boswick Lane"}
    # time.sleep(60)
    scraper = WasteCollectionScraper(headless=True)
    data = scraper.find_collection_dates(CONFIG["url"], CONFIG["postcode"], CONFIG["address"])
    if data:
        scraper.sync_to_google_calendar(data)