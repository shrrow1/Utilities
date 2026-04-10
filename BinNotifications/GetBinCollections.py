import time
import datetime
import os.path
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Google Calendar API Imports
# Requires: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


class WasteCollectionScraper:
    WAIT_TIMEOUT = 5
    # Permission scope for managing calendar events
    SCOPES = ['https://www.googleapis.com/auth/calendar.events']

    def __init__(self, headless=True):
        """
        Initializes the Selenium WebDriver with headless mode and suppressed logging.
        """
        self.chrome_options = Options()

        # 1. SUPPRESS VISIBLE WINDOW
        if headless:
            self.chrome_options.add_argument("--headless=new")

        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--window-size=1920,1080")

        # 2. SUPPRESS CONSOLE ERRORS
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.chrome_options.add_argument("--log-level=3")
        self.chrome_options.add_argument("--silent")

        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.wait = WebDriverWait(self.driver, 15)

    def find_collection_dates(self, url, postcode, address_substring):

        try:
            print(f"Navigating to {url}...")
            self.driver.get(url)

            # Handle Cookie Consent
            try:
                cookie_accept_button = WebDriverWait(self.driver, self.WAIT_TIMEOUT).until(
                    EC.element_to_be_clickable((By.ID, 'newConsentGranted'))
                )
                cookie_accept_button.click()
            except (TimeoutException, NoSuchElementException):
                pass

            # Enter Postcode
            postcode_input = self.wait.until(EC.visibility_of_element_located((By.ID, "txtBxPCode")))
            postcode_input.clear()
            postcode_input.send_keys(postcode)
            self.driver.find_element(By.ID, "btnFindAddr").click()

            # Select Address
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
                print(f"Could not find address containing '{address_substring}'")
                return None

            # Click Show Collections
            time.sleep(1)
            self.driver.find_element(By.ID, "MainContent_btnGetSchedules").click()

            # Wait for results
            self.wait.until(EC.presence_of_element_located((By.ID, "lblSelectedAddr")))

            print("Scraping and grouping results...")
            results = {}

            bin_headers = self.driver.find_elements(By.XPATH,
                                                    "//strong[contains(translate(text(), 'BIN', 'bin'), 'bin')]")

            for header in bin_headers:
                try:
                    bin_type = header.text.strip()
                    parent = header.find_element(By.XPATH, "./ancestor::div[contains(@style, 'margin:5px')][1]")
                    date_element = parent.find_element(By.XPATH,
                                       ".//div[contains(text(), 'Next collection on:')]/following-sibling::div")

                    raw_date = date_element.text.strip()
                    bin_date = raw_date.split(', ')[1] if ',' in raw_date else raw_date

                    if bin_date in results:
                        results[bin_date] = f"{results[bin_date]} & {bin_type}"
                    else:
                        results[bin_date] = bin_type

                    print(f"Found: {bin_date} -> {results[bin_date]}")
                except (NoSuchElementException, IndexError):
                    continue

            return results

        except Exception as e:
            print(f"An error occurred during scraping: {e}")
            return None
        finally:
            print("Closing browser...")
            self.driver.quit()

    def sync_to_google_calendar(self, data):
        """
        Authenticates and adds the scraped dates as all-day events.
        Optimized to only check for existing events on the specific collection days.
        """
        if not data:
            print("No data to sync.")
            return

        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    print("Error: 'credentials.json' not found.")
                    return
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)

            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('calendar', 'v3', credentials=creds)

        print("\nSyncing to Google Calendar...")
        for date_str, bin_info in data.items():
            try:
                date_obj = datetime.datetime.strptime(date_str, "%d %b %Y")
                iso_date_start = date_obj.strftime("%Y-%m-%d")

                # For all-day events, 'end' date is exclusive (day after start)
                iso_date_end = (date_obj + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

                summary = f'Bins: {bin_info}'

                # Optimized Check: Only fetch events for this specific day
                time_min = f"{iso_date_start}T00:00:00Z"
                time_max = f"{iso_date_start}T23:59:59Z"

                events_result = service.events().list(
                    calendarId='primary',
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True
                ).execute()

                existing_events = events_result.get('items', [])

                # Check if an event with this exact summary already exists on this day
                is_duplicate = any(event.get('summary') == summary for event in existing_events)

                if is_duplicate:
                    print(f"Skipping: Event already exists for {iso_date_start} ({bin_info})")
                else:
                    event = {
                        'summary': summary,
                        'description': f'Automated collection reminder for: {bin_info}',
                        'start': {'date': iso_date_start},
                        'end': {'date': iso_date_end},
                        'reminders': {
                            'useDefault': False,
                            'overrides': [
                                {'method': 'email', 'minutes': 24 * 60},
                            ],
                        },
                    }

                    service.events().insert(calendarId='primary', body=event).execute()
                    print(f"Created event: {iso_date_start} - {bin_info}")

            except Exception as e:
                print(f"Failed to process event for {date_str}: {e}")


if __name__ == "__main__":
    # TODO: Move to config file
    TARGET_URL = "https://webapps.dacorum.gov.uk/bincollections"
    MY_POSTCODE = "HP4 3TH"
    MY_HOUSE = "8 Boswick Lane"

    scraper = WasteCollectionScraper(headless=True)
    scraped_data = scraper.find_collection_dates(TARGET_URL, MY_POSTCODE, MY_HOUSE)

    if scraped_data:
        print("\n--- Summary of Collections Found ---")
        for d, b in scraped_data.items():
            print(f"{d}: {b}")

        scraper.sync_to_google_calendar(scraped_data)
    else:
        print("Scraping failed or no data returned.")
