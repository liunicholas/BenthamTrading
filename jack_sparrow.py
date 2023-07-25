import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import trading_clock as tc
import datetime
import pandas as pd
import numpy as np

INTERVAL = 5

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument('--blink-settings=imagesEnabled=false')

class JackSparrow():
    def __init__(self, name, data_url):
        self.name = name
        self.data_url = data_url
        self.driver = self.initialize_driver()
        self.data_file_path = f"data/{self.name}_{tc.real_time().date()}.csv"
        
        if os.path.exists(self.data_file_path):
            print(f"[INFO] Reading Already Made DataFrame for {name} \n")
            self.day_df = pd.read_csv(self.data_file_path, index_col=0, parse_dates=True)
        
        else:
            print(f"[INFO] Making New DataFrame for {name} \n")
            date = tc.real_time().date()
            start = tc.localize(datetime.datetime.combine(date, datetime.time(9, 30, 0)))
            date_range = pd.date_range(start, start + datetime.timedelta(hours=6, minutes=25), freq=datetime.timedelta(minutes=INTERVAL))

            open = np.empty((len(date_range)))
            open[:] = np.nan
            high = np.empty((len(date_range)))
            high[:] = -1
            low = np.empty((len(date_range)))
            low[:] = float("inf")
            close = np.empty((len(date_range)))
            close[:] = np.nan

            self.day_df = pd.DataFrame({'Date': date_range, 'Open': open, "High": high, "Low": low, "Close": close}).set_index('Date')
    
    def initialize_driver(self):
        print(f"[INFO] Initializing Driver For {self.name}")
        driver = webdriver.Chrome(options=options)
        driver.get(self.data_url)

        return driver

    def scrape_moment(self):
        while True:
            try:
                # current_price = float(self.driver.execute_script("""
                # return Array.prototype.slice.call(document.getElementsByClassName("last-JWoJqCpY"));
                # """)[0].text)
                # print(current_price)
                current_price = float(self.driver.find_element(By.CLASS_NAME, "last-value").text)
            except Exception as exception:
                print("Bad price request, trying again")
                print(exception)
                self.driver = self.initialize_driver(self.data_url)
            else:
                break

        current_datetime = tc.real_time()
        try:
            # add open price
            if np.isnan(self.day_df["Open"][[tc.last_five_minute(
                    tc.real_time())]].item()):
                self.day_df["Open"][[tc.last_five_minute(
                    tc.real_time())]] = current_price
        except:
            print("[INFO] Key error, likely last 5 minute interval of the day at 4:00")
            return
  
        if current_price > self.day_df["High"][[tc.last_five_minute(current_datetime)]].item():
            self.day_df["High"][[tc.last_five_minute(
                tc.real_time())]] = current_price
        if current_price < self.day_df["Low"][[tc.last_five_minute(current_datetime)]].item():
            self.day_df["Low"][[tc.last_five_minute(
                tc.real_time())]] = current_price

        self.day_df["Close"][[tc.last_five_minute(
            current_datetime)]] = current_price

        # self.day_df.dropna().to_csv(self.data_file_path )
        self.day_df.to_csv(self.data_file_path)

def scrape_day():

    spxFUTURESscraper = JackSparrow(
        "spxFUTURES", "https://www.cmegroup.com/markets/equities/sp/e-mini-sandp500.html")
    ndqFUTURESscraper = JackSparrow(
        "ndqFUTURES", "https://www.cmegroup.com/markets/equities/nasdaq/e-mini-nasdaq-100.html")
    
    print("[INFO] Scraping Now")

    last_known_minute = -1
    while tc.is_market_open(security_type="ETF", current_datetime=tc.real_time()):
        current_time = tc.real_time()
        if current_time.minute != last_known_minute and current_time.minute % INTERVAL == 0:
            print(f"[INFO] Scraper Active Last At {current_time}")
            last_known_minute = current_time.minute
        if current_time.time() >= tc.NYSE_close:
            print("[INFO] Exchange Closed")
            break

        spxFUTURESscraper.scrape_moment()
        ndqFUTURESscraper.scrape_moment()

    print("[INFO] Finished Scraping Day")
        
def main():
    LIVE = True
    last_known_minute = -1
    while LIVE:
        current_time = tc.real_time()
        if current_time.minute != last_known_minute and current_time.minute % INTERVAL == 0:
            last_known_minute = current_time.minute

            if tc.is_market_open(security_type="ETF", current_datetime=current_time, VERBOSE=True):
                print("MARKET OPENED")
                scrape_day()

            else:
                print("MARKET CLOSED")

if __name__ == "__main__":
    main()
