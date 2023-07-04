import time
import os
from selenium import webdriver
import trading_clock as tc
import datetime
import pandas as pd
import numpy as np
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

options = webdriver.ChromeOptions()
options.add_argument("window-size=1440, 751")
options.add_argument("--profile-directory=Profile 10")
options.add_argument("--headless")

spxCFDdriver = webdriver.Chrome(options=options)
spxCFDdriver.get("https://www.tradingview.com/symbols/EIGHTCAP-SPX500/")

ndqCFDdriver = webdriver.Chrome(options=options)
ndqCFDdriver.get("https://www.tradingview.com/symbols/EIGHTCAP-NDQ100/")

spxFUTURESdriver = webdriver.Chrome(options=options)
spxFUTURESdriver.get("https://www.tradingview.com/symbols/CME_MINI-ES1!/")

ndqFUTURESdriver = webdriver.Chrome(options=options)
ndqFUTURESdriver.get("https://www.tradingview.com/symbols/CME_MINI-NQ1!/")

class JackSparrow():
    def __init__(self, name, driver):
        self.name = name
        self.driver = driver
        self.data_file_path = f"data/{self.name}_{tc.real_time().date()}.csv"
        
        if os.path.exists(self.data_file_path):
            self.day_df = pd.read_csv(self.data_file_path, index_col=0)
        else:
            date = tc.real_time().date()
            start = tc.localize(datetime.datetime.combine(date, datetime.time(9, 35, 0)))
            date_range = pd.date_range(start, start + datetime.timedelta(hours=6, minutes=25), freq=datetime.timedelta(minutes=5))

            open = np.empty((len(date_range)))
            open[:] = np.nan
            high = np.empty((len(date_range)))
            high[:] = -1
            low = np.empty((len(date_range)))
            low[:] = float("inf")
            close = np.empty((len(date_range)))
            close[:] = np.nan

            self.day_df = pd.DataFrame(
                {'Date': date_range, 'Open': open, "High": high, "Low": low, "Close": close}).set_index('Date')
            # self.day_df = self.day_df.set_index('Date')
    
    def scrape_moment(self):
        while True:
            try:
                current_price = float(self.driver.execute_script("""
                return Array.prototype.slice.call(document.getElementsByClassName("last-JWoJqCpY"));
                """)[0].text)
                # print(current_price)
            except:
                print("Bad price request, trying again")
            else:
                break

        current_datetime = tc.real_time()
        if (current_datetime.minute) % 5 == 0 and current_datetime.second == 0:
            self.day_df["Open"][[tc.next_five_minute(
                tc.real_time())]] = current_price
            self.day_df["High"][[tc.next_five_minute(
                tc.real_time())]] = current_price
            self.day_df["Low"][[tc.next_five_minute(
                tc.real_time())]] = current_price

        if current_price > self.day_df["High"][[tc.next_five_minute(tc.real_time())]].item():
            self.day_df["High"][[tc.next_five_minute(
                tc.real_time())]] = current_price
        if current_price < self.day_df["Low"][[tc.next_five_minute(tc.real_time())]].item():
            self.day_df["Low"][[tc.next_five_minute(
                tc.real_time())]] = current_price

        self.day_df["Close"][[tc.next_five_minute(tc.real_time())]] = current_price

        # self.day_df.dropna().to_csv(f"data/{self.name}_{tc.real_time().date()}.csv")
        self.day_df.to_csv(self.data_file_path)

def scrape_day():

    spxCFDscraper = JackSparrow("spxCFD", spxCFDdriver)
    ndqCFDscraper = JackSparrow("ndqCFD", ndqCFDdriver)
    spxFUTURESscraper = JackSparrow("spxFUTURES", spxFUTURESdriver)
    ndqFUTURESscraper = JackSparrow("ndqFUTURES", ndqFUTURESdriver)
    
    while tc.is_market_open(security_type="ETF", current_datetime=tc.real_time()):
        spxCFDscraper.scrape_moment()
        ndqCFDscraper.scrape_moment()
        spxFUTURESscraper.scrape_moment()
        ndqFUTURESscraper.scrape_moment()
        
def main():
    LIVE = True
    last_known_minute = -1
    while LIVE:
        current_time = tc.real_time()
        if current_time.minute != last_known_minute:
            last_known_minute = current_time.minute

            if tc.is_market_open(security_type="ETF", current_datetime=current_time, VERBOSE=True):
                print("MARKET OPENED")
                scrape_day()

            else:
                print("MARKET CLOSED")

if __name__ == "__main__":
    main()
