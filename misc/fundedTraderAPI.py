from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# Create a new instance of the Chrome driver
driver = webdriver.Chrome()

# Navigate to site
driver.get("https://mit.clubautomation.com/")

# Find the search input element and enter the search query

# search_input.send_keys('never gonna give you up')

search_input = driver.find_element('id', 'loginButton')
search_input.send_keys(Keys.RETURN)

# Find the first search result and click on it
# first_result = driver.find_element('id', 'video-title')
# first_result.click()

while (True):
    pass

# Close the browser
# driver.quit()
