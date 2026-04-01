"""
https://realpython.com/modern-web-automation-with-python-and-selenium/#implement-the-page-object-model-pom
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager # Highly recommended for easier setup
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


chrome_options = Options()
# chrome_options.add_argument("--headless")

# Disable the "Chrome is being controlled by automated test software" banner
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

# Disable the logging for a cleaner console output (optional)
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

# Add a User-Agent that resembles a real browser (optional, but good practice)
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
chrome_options.add_argument(f'user-agent={user_agent}')

# driver = webdriver.Chrome(options=chrome_options)
service = ChromeService(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 3. Execute the key anti-detection JavaScript
#    This command removes the 'navigator.webdriver' property from the browser environment.
driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
          """
    }
)

# driver = webdriver.Firefox()  # Run in normal mode
driver.implicitly_wait(1)

driver.get("https://webapps.dacorum.gov.uk/bincollections/")

# Accept cookies, if required
try:
    cookie_accept_button = driver.find_element(
        By.CSS_SELECTOR,
        "#newConsentGranted",
    )
    cookie_accept_button.click()
except NoSuchElementException:
    pass


# time.sleep(0.5)
#
search = driver.find_element(By.ID, "MainContent_pnlSearchAddr")
search_field = search.find_element(By.ID, "txtBxPCode")
search_field.send_keys("hp4 3th")
search_button = search.find_element(By.ID, "btnFindAddr")
search_button.click()

time.sleep(2)
try:
    # This line tells Selenium to wait up to 10 seconds (WAIT_TIMEOUT) until
    # the element with the specified ID is visible on the page.
    address_list = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, '#MainContent_lblPlsSelAddr'))
    )
    print("SUCCESS: Address list found!")

# Now you can safely interact with the address list element
# Example: print the content (if you need to)
# print(address_list.text)

except Exception as e:
    # This block executes if the element is not found within the timeout
    print("FAILURE: Address list did not appear or disappeared too quickly within the timeout.")
    print(f"Error details: {e}")
    # driver.quit()

addresses_list = driver.find_element(By.ID, "lstBxAddrList")
address_select = Select(addresses_list)

for option in address_select.options:
    print(option.text)

time.sleep(5)

driver.quit()