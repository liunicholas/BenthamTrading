from trader import *
import trading_clock as tc
from datetime import datetime, date, time, timedelta
import yfinance as yf
import pytz
import time

datetime_range = [tc.localize(datetime(2023, 6, 8, 6, 30, 0)),
                  tc.localize(datetime(2023, 6, 8, 24, 0, 0))]

currentTime = datetime_range[0]
waitTime = 0

while currentTime < datetime_range[-1]:
    tc.override(currentTime)
    
    do runday stuff here

    time.sleep()
    currentTime += timedelta(minutes=1)
    