import trading_clock as tc
import yfinance as yf
from twelvedata import TDClient
from datetime import timedelta, datetime
import pandas as pd
from time import sleep

# main key
twelvedata_api_key = '118aed5a291f4a9fb7c36cfb590db853'

# backup key
backup_twelvedata_api_key = "a7ae2e81f8d74438bd9f6a5e08cebef3"

class SecurityData:
    def __init__(self, security):
        self.data_master = {}
        self.security = security
    
    def get_day_data(self, day_name, current_time, interval, delta):
        current_date = current_time.date()
        desired_date = tc.get_delta_trading_date(self.security, current_date, delta)
    
        if desired_date > tc.get_today().date():
            print("[ERROR] Bad day data request: date is in the future.")
        elif delta == 0:
            self.data_master[day_name] = self.get_today_data(current_time, interval)
        else:
            self.data_master[day_name] = self.get_yfinance_data(desired_date, desired_date+timedelta(days=1), interval)
    
    def __getitem__(self, day_name):
        return self.data_master[day_name]

    def get_today_data(self, current_time, interval):
        # backtesting_flag = False
        if (datetime.now(tc.new_york_tz) - current_time) < timedelta(minutes=30): # 30 second tolerance
            # TODO: if shit breaks, look here because twelve data may only get 2hr 30 min worth of data back
            today_data = self.get_twelve_data(
                start=current_time.date(), 
                end=tc.get_delta_trading_date(self.security, current_time.date(), 1), 
                interval=interval
            )
            # #live data
            # if (datetime.now(tc.new_york_tz) - current_time) < timedelta(seconds=30):
            #     backtesting_flag = False
            # # back testing data 
            # else:
            #     backtesting_flag = True
        else: # back testing data
            # backtesting_flag = True
            today_data = self.get_yfinance_data(start=current_time.date(), end=tc.get_delta_trading_date(
                self.security, current_time.date(), 1), interval=interval)
        
        # if backtesting_flag:
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
        
        return day_data

    def get_twelve_data(self, start, end, interval):
        if self.security == "^spx":
            security = "gspc"
        else:
            security = self.security

        GOOD_DATA = False
        try:
            time_data_client = TDClient(apikey=twelvedata_api_key)
            day_data = time_data_client.time_series(
                symbol=security,
                interval=f"{interval}min",
                timezone=tc.new_york_tz,
                start_date=start,
                end_date=end,
            ).as_pandas()
        except:
            try:
                sleep(5)
                time_data_client = TDClient(apikey=backup_twelvedata_api_key)
                day_data = time_data_client.time_series(
                    symbol=security,
                    interval=f"{interval}min",
                    timezone=tc.new_york_tz,
                    start_date=start,
                    end_date=end,
                ).as_pandas()
            except:
                print("DATA IS FUCKED UP (or there is just no data for the day yet)")
                exit()
            else:
                GOOD_DATA = True
        else:
            GOOD_DATA = True

        if GOOD_DATA:
            day_data.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume',
                }, inplace=True)
            # day_data.index = day_data.index.tz_localize('UTC')
            # if not day_data.empty:
            day_data.index = day_data.index.tz_localize(tc.new_york_tz)

            day_data = day_data.iloc[::-1]
            return day_data
        
        else:
            return pd.DataFrame()


if __name__ == "__main__":
    SPXdata = SecurityData(security="^spx")
    SPXdata.get_day_data("yesterdata",tc.get_today()-timedelta(days=1), interval=5, delta=-1)
    print(SPXdata["yesterdata"])