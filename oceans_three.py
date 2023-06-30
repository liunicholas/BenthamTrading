import cv2
import pytesseract
import time
from selenium import webdriver
import trading_clock as tc
import datetime
import pandas as pd
import numpy as np
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

options = webdriver.ChromeOptions()
options.add_argument("window-size=1440, 751")
# options.add_argument("--profile-directory=Profile 10")
# options.add_argument("--headless")
# options.add_argument("user-data-dir=/Users/jameshou/Library/Application Support/Google/Chrome/User Data")
driver = webdriver.Chrome(options=options)
driver.maximize_window()
driver.get('https://www.tradingview.com/chart/?symbol=EIGHTCAP%3ASPX500')
# elem = driver.find_element(By.CSS_SELECTOR, "body")
# ac = ActionChains(driver)
# ac.move_by_offset(440, 40).click().perform()
time.sleep(5)


screenshot_interval = 1
while True:
    date = tc.get_today().date()
    start = tc.localize(datetime.datetime.combine(date, datetime.time(9, 35, 0)))
    date_range = pd.date_range(start, start + datetime.timedelta(hours=6, minutes=25), freq=datetime.timedelta(minutes=5))

    open = np.empty((len(date_range)))
    open[:] = np.nan
    high = np.empty((len(date_range)))
    high[:] = np.nan
    low = np.empty((len(date_range)))
    low[:] = np.nan
    close = np.empty((len(date_range)))
    close[:] = np.nan
    
    day_df = pd.DataFrame({'index': date_range, 'Open':open, "High":high, "Low":low, "Close":close})
    day_df = day_df.set_index('index')
    while True:
    # while tc.is_market_open(current_datetime=tc.get_today()):
        timer = time.time()
        print((tc.next_five_minute(tc.get_today()) - tc.get_today()).total_seconds())
        if (tc.next_five_minute(tc.get_today()) - tc.get_today()).total_seconds() <= 1.0:
            time.sleep((tc.next_five_minute(tc.get_today()) - tc.get_today()).total_seconds() - 0.6)
        else:
            time.sleep(screenshot_interval)

        driver.get_screenshot_as_file("tradingview.png")
        image = cv2.imread(r'tradingview.png')
        width = image.shape[1]
        height = image.shape[0]
        image = image[100:150, 750:1530, :]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, config="--psm 6")
        
        data = text.split(" ")
        entry = {"Open": float(data[0][1:]), "High": float(data[1][1:]), "Low": float(data[2][1:]), "Close": float(data[3][1:])}
        print(entry)
        day_df["Open"][[tc.last_five_minute(tc.get_today())]] = entry["Open"]
        day_df["High"][[tc.last_five_minute(tc.get_today())]] = entry["High"]
        day_df["Low"][[tc.last_five_minute(tc.get_today())]] = entry["Low"]
        day_df["Close"][[tc.last_five_minute(tc.get_today())]] = entry["Close"]


        print(day_df.loc[[tc.last_five_minute(tc.get_today())]])

        day_df.dropna().to_csv(f"data/{tc.get_today().date()}.csv")
        print(time.time() - timer)