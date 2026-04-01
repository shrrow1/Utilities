import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

WAIT_TIMEOUT=1

chrome_options = Options()
# chrome_options.add_argument("--headless")

driver = webdriver.Chrome(options=chrome_options)  # Run in normal mode

driver.implicitly_wait(WAIT_TIMEOUT)

driver.get("https://webapps.dacorum.gov.uk/bincollections/")

# Accept cookies, if required
try:
# This line tells Selenium to wait up to 10 seconds (WAIT_TIMEOUT) until
# the element with the specified ID is visible on the page.

    cookie_accept_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, 'newConsentGranted'))
    )
    cookie_accept_button.click()

except TimeoutException  as e:
    pass

# cookie_accept_button = driver.find_element(
#     By.CSS_SELECTOR,
#     "#newConsentGranted",
# )
# cookie_accept_button.click()

# time.sleep(22)
search = driver.find_element(By.ID, "MainContent_pnlSearchAddr")
search_field = search.find_element(By.ID, "txtBxPCode")
search_field.send_keys("hp4 3th")
search_button = search.find_element(By.ID, "btnFindAddr")
search_button.click()

try:
    # This line tells Selenium to wait up to 10 seconds (WAIT_TIMEOUT) until
    # the element with the specified ID is visible on the page.
    address_select = Select(WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, 'lstBxAddrList')))
    )

except Exception as e:
    # This block executes if the element is not found within the timeout
    print("FAILURE: Address list did not appear or disappeared too quickly within the timeout.")
    print(f"Error details: {e}")
    # driver.quit()

for option in address_select.options:
    print(option.text)
    if option.text.startswith('8 Boswick Lane'):
        option.click()
        break

address_select_button = driver.find_element(By.ID, "MainContent_btnGetSchedules")
address_select_button.click()

results = Select(WebDriverWait(driver, WAIT_TIMEOUT).until(
    EC.presence_of_element_located((By.ID, 'MainContent_updPnl')))
)

self.wait.until(EC.presence_of_element_located((By.ID, "MainContent_updPnl")))

driver.quit()






#
#
#
#     <br>
#     <span id="lblSelectedAddr" style="font-weight:bold;">Bin collection schedule for 8 Boswick Lane Dudswell Berkhamsted
#         Hertfordshire HP4 3TH .<br></span>
#
#
#     <br>
#
#
#
#     <span>Your usual collection day is <strong>Thursday</strong></span>
#     <div style=" margin:5px;">
#         <div style="display:inline-block;padding-left: 10px;"><strong>Grey bin and kerbside caddy</strong></div>
#         <div style="display:table; border-spacing: 10px;">
#             <div style="display:table-row;">
#                 <div style="display:table-cell;">Next collection on: </div>
#                 <div style="display:table-cell;">Thu, 23 Oct 2025</div>
#             </div> <!--ROW-->
#         </div>
#     </div>
#     <hr>
#     <div style=" margin:5px;">
#         <div style="display:inline-block;padding-left: 10px;"><strong>Green bin</strong></div>
#         <div style="display:table; border-spacing: 10px;">
#             <div style="display:table-row;">
#                 <div style="display:table-cell;">Next collection on: </div>
#                 <div style="display:table-cell;">Thu, 23 Oct 2025</div>
#             </div> <!--ROW-->
#         </div>
#     </div>
#     <hr>
#     <div style=" margin:5px;">
#         <div style=" margin:5px;">
#             <div style="display:inline-block;padding-left: 10px;"><strong>Blue bin and kerbside caddy</strong></div>
#             <div style="display:table; border-spacing: 10px;">
#                 <div style="display:table-row;">
#                     <div style="display:table-cell;">Next collection on: </div>
#                     <div style="display:table-cell;">Thu, 30 Oct 2025</div>
#                 </div> <!--ROW-->
#             </div>
#         </div>
#         <hr>
#         <div style=" margin:5px;">
#             <div style="display:table-row;">
#                 <div style="display:table-cell;"><a class="button"
#                         href="https://www.dacorum.gov.uk/docs/default-source/environment-street-care/2024-2025-waste-collection-calendar---thursday---odds.pdf"
#                         title="Download your waste collection calendar"><img style="vertical-align: bottom;"
#                             src="http://www.dacorum.gov.uk/images/default-source/web-graphics/download_32.gif?sfvrsn=2"
#                             alt="">Download your waste collection calendar</a></div>
#             </div>
#             <p><strong>Please note: We may collect your waste on a different day over bank holidays.</strong></p>
#         </div>
#     </div>
# </div>