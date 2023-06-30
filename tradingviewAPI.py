from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

# Create a new instance of the Chrome driver
driver = webdriver.Chrome()

# Navigate to site
driver.get("https://www.tradingview.com/symbols/CBOE-SPX/")

# Find the search input element and enter the search query

# search_input.send_keys('never gonna give you up')
# text = driver.find_element(By.XPATH("//span[@class='last-JWoJqCpY']"))
while True:
    text = driver.execute_script("""
    return Array.prototype.slice.call(document.getElementsByClassName("last-JWoJqCpY"));
    """)[0].text
    print(text)
# search_input = driver.find_element('id', 'loginButton')
# search_input.send_keys(Keys.RETURN)

# Find the first search result and click on it
# first_result = driver.find_element('id', 'video-title')
# first_result.click()

# while True:
#     pass

# Close the browser
# driver.quit()
