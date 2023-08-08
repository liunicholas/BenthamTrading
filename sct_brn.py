import os
import trading_clock as tc
import datetime
import pandas as pd
import numpy as np
import discord
from discord.ext import tasks
import re
import ast

INTERVAL = 5

intents = discord.Intents(messages=True, message_content=True, guilds=True)
client = discord.Client(intents=intents)
TOKEN = "MTEyMTE1MzI3MjE3MDk0NjU5Mg.G3qbyD.-IhGrjmcKp4e_d3H2A7xwlXSNzmiOVuyvKslhA"
spxFUTURESdata = None
ndqFUTURESdata = None

@client.event
async def harden_stepback(message):
    def get_dict_from_string(s):
        # Extract the dictionary string using regular expressions
        match = re.search(r'\{.*\}', s)
        if match:
            dict_string = match.group(0)
            # Convert the dictionary string to a dictionary using ast.literal_eval
            data_dict = ast.literal_eval(dict_string)
            # print(data_dict)
            return data_dict
        else:
            print("No dictionary found in the string.")

    global spxFUTURESdata
    global ndqFUTURESdata
    is_market_open = tc.is_market_open(security_type="ETF", current_datetime=tc.real_time())
    if (message.channel.id==1138302357927641098) and is_market_open:
        security = message.split(":")[0].strip()
        security_data = get_dict_from_string(message)
        data_time_index = tc.last_five_minute(tc.real_time())
        # try updating spxFUTURESdata
        if security == "spx futures" and spxFUTURESdata.date == tc.real_time().date():
            spxFUTURESdata.day_df["Open"][[data_time_index]] = security_data["Open"]
            spxFUTURESdata.day_df["High"][[data_time_index]] = security_data["High"]
            spxFUTURESdata.day_df["Low"][[data_time_index]] = security_data["Low"]
            spxFUTURESdata.day_df["Close"][[data_time_index]] = security_data["Close"]

            spxFUTURESdata.day_df.to_csv(spxFUTURESdata.data_file_path)

        #try updating ndqFUTURESdata
        elif security == "ndq futures" and ndqFUTURESdata.date == tc.real_time().date():  
            ndqFUTURESdata.day_df["Open"][[data_time_index]] = security_data["Open"]
            ndqFUTURESdata.day_df["High"][[data_time_index]] = security_data["High"]
            ndqFUTURESdata.day_df["Low"][[data_time_index]] = security_data["Low"]
            ndqFUTURESdata.day_df["Close"][[data_time_index]] = security_data["Close"]

            ndqFUTURESdata.day_df.to_csv(spxFUTURESdata.data_file_path)

        else:
            print("[ERROR] data retrieval flopped")

class ScottBarnes():
    def __init__(self, name):
        self.name = name
        self.date = tc.real_time().date()
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
            high[:] = np.nan
            low = np.empty((len(date_range)))
            low[:] = np.nan
            close = np.empty((len(date_range)))
            close[:] = np.nan

            self.day_df = pd.DataFrame({'Date': date_range, 'Open': open, "High": high, "Low": low, "Close": close}).set_index('Date')  

def scrape_day():
    global spxFUTURESdata 
    spxFUTURESdata = ScottBarnes("spxFUTURES")
    global ndqFUTURESdata 
    ndqFUTURESdata = ScottBarnes("ndqFUTURES")

    print("[INFO] Starting to Scrape Day")

    last_known_minute = -1
    while tc.is_market_open(security_type="ETF", current_datetime=tc.real_time()):
        current_time = tc.real_time()
        if current_time.minute != last_known_minute and current_time.minute % INTERVAL == 0:
            print(f"[INFO] Scraper Active Last At {current_time}")
            last_known_minute = current_time.minute
        if current_time.time() >= tc.NYSE_close:
            print("[INFO] Exchange Closed")
            break

    print("[INFO] Finished Scraping Day")
        
def main():
    LIVE = True
    last_known_minute = None
    while LIVE:
        client.run(TOKEN)
        current_time = tc.real_time()
        if last_known_minute is None or (current_time.minute != last_known_minute and current_time.minute % INTERVAL == 0):
            last_known_minute = current_time.minute

            if tc.is_market_open(security_type="ETF", current_datetime=current_time, VERBOSE=True):
                print("MARKET OPENED")
                scrape_day()

            else:
                print("MARKET CLOSED")

if __name__ == "__main__":
    main()
