import requests
from bs4 import BeautifulSoup
import trading_clock as tc
import yfinance as yf
from twelvedata import TDClient
from datetime import timedelta, datetime
import pandas as pd
from time import sleep

# twelvedata keys
twelvedata_api_key_1 = '118aed5a291f4a9fb7c36cfb590db853'
twelvedata_api_key_2 = "a7ae2e81f8d74438bd9f6a5e08cebef3"
twelvedata_api_key_3 = "2e6d6dfac96b4ab1b4c5540d3c448b0b"

twelvedata_keys = [twelvedata_api_key_1,
                   twelvedata_api_key_2, 
                   twelvedata_api_key_3]

class SecurityData:
    def __init__(self, security):
        self.data_master = {}
        self.security = security
    
    def get_day_data(self, day_name, current_time, interval, delta):
        current_date = current_time.date()
        desired_date = tc.get_delta_trading_date(self.security, current_date, delta)
    
        if desired_date > tc.real_time().date():
            print("[ERROR] Bad day data request: date is in the future.")
        elif delta == 0:
            self.data_master[day_name] = self.get_today_data(current_time, interval)
        else:
            self.data_master[day_name] = self.get_yfinance_data(desired_date, desired_date+timedelta(days=1), interval)
    
    def __getitem__(self, day_name):
        return self.data_master[day_name]

    def get_today_data(self, current_time, interval):
        # only use twelvedata when we actually need the live data
        today_data_twelvedata = pd.DataFrame()
        # 30 minute tolerance to delayed yfinance data
        if (tc.real_time() - current_time) < timedelta(minutes=30):  
            today_data_twelvedata = self.get_twelve_data(
                start=current_time.date(), 
                end=tc.get_delta_trading_date(self.security, current_time.date(), 1), 
                interval=interval
            )

        today_data_yfinance = self.get_yfinance_data(start=current_time.date(), end=tc.get_delta_trading_date(
                self.security, current_time.date(), 1), interval=interval)
        
        # combine twelvedata and yfinance if necessary
        if not today_data_twelvedata.empty:
            twelvedata_first_time = today_data_twelvedata.index[0].to_pydatetime()
            temp = []
            for i, row in today_data_yfinance.iterrows():
                if i < twelvedata_first_time:
                    temp.append(row)
            if temp:
                today_data_yfinance = pd.concat(temp, axis=1).T
                today_data = pd.concat(
                    [today_data_yfinance, today_data_twelvedata], ignore_index=False)
            else:
                today_data = today_data_twelvedata
        else:
            today_data = today_data_yfinance

        
        # filter today_data up to the current_time
        temp = []
        for i, row in today_data.iterrows():
            if i+timedelta(minutes=interval) <= current_time:
                temp.append(row)
        if temp:
            today_data = pd.concat(temp, axis=1).T
        else:
            today_data = pd.DataFrame()

        return today_data

    def get_yfinance_data(self, start, end, interval):
        day_data = yf.download(
            progress=False,
            tickers=self.security,
            start=start,
            end=end,
            interval=f'{interval}m'
        )
        day_data = day_data.drop('Adj Close', axis=1)

        if day_data.empty:
            print("[ERROR] No data found for this query")
            print("[SUGGESTION] run 'pip install yfinance --upgrade --no-cache-dir'")
        
        return day_data

    def get_twelve_data(self, start, end, interval):
        if self.security == "^spx":
            security = "gspc"
        elif self.security == "^ixic":
            security = "ixic"
        else:
            security = self.security

        API_SUCCESS = False
        for i, apikey in enumerate(twelvedata_keys):
            if not API_SUCCESS:
                try:
                    time_data_client = TDClient(apikey=apikey)
                    day_data = time_data_client.time_series(
                        symbol=security,
                        interval=f"{interval}min",
                        timezone=tc.new_york_tz,
                        start_date=start,
                        end_date=end,
                    ).as_pandas()
                except:
                    print("[INFO/ERROR] Trying new API key")
                else:
                    API_SUCCESS = True
                    print(f"[INFO] Data Successfully Retrieved for {security} with API key {i+1}")

                    # clean data
                    day_data.rename(columns={
                        'open': 'Open',
                        'high': 'High',
                        'low': 'Low',
                        'close': 'Close',
                        'volume': 'Volume',
                    }, inplace=True)
                    day_data.index = day_data.index.tz_localize(tc.new_york_tz)

                    #reverse order of time series data
                    day_data = day_data.iloc[::-1]
                    return day_data
        
        if not API_SUCCESS:
            print("[ERROR] All API keys failed")
            return pd.DataFrame()

def get_economic_news():
    # url = 'https://us.econoday.com/byweek.asp?cust=us'
    # html = requests.get(url).content
    # df_list = pd.read_html(html)
    # # df = df_list[-1]
    # print(df_list)
    # # df.to_csv('my data.csv')

    # URL of the website with the tables
    # url = 'https://us.econoday.com/byweek.asp?cust=us'
    url = "https://www.forexfactory.com"
    # Send a GET request to the website
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all the tables on the page
        # tables = soup.find_all('table')

        table = soup.find_all('table', {"class": "calendar__table  "})[0]

        # Process each table
        if table:
            # Extract table headers
            headers = [header.text for header in table.find_all('th')]
            print('Table Headers:', headers)

            # Extract table rows
            rows = table.find_all('tr')

            # Process each row
            for row in rows:
                # Extract table cells
                cells = row.find_all('td')
                values = [cell.text for cell in cells]
                print('Row Values:', values)

            print('-' * 50)
    else:
        print('Error: Unable to retrieve data from the website.')

if __name__ == "__main__":
    SPXdata = SecurityData(security="^spx")
    SPXdata.get_day_data("yesterdata",tc.get_today()-timedelta(days=1), interval=5, delta=-1)
    print(SPXdata["yesterdata"])