import numpy as np
import pandas as pd

# Data Source
import yfinance as yf

# Data viz
import plotly.graph_objs as go
from datetime import datetime, time, timedelta

daydata = yf.download(tickers='^SPX', period='2d', interval='1d')
data5min = yf.download(tickers='^SPX', period='1d', interval='5m')

p_buyside_liquidity = daydata["High"][0]
p_sellside_liquidity = daydata["Low"][0]

tp1_open = datetime(2023, 6, 6, 10, 0, 0)
tp1_close = datetime(2023, 6, 6, 11, 0, 0)

tp2_open = datetime(2023, 6, 6, 14, 0, 0)

tp2_close = datetime(2023, 6, 6, 15, 0, 0)

fivemin = '00:05:00'
format = '%H:%M:%S'
fivemin = datetime.strptime(fivemin, format)


dips = []
breaches = []
# tp1
for i, row in data5min.iterrows():
    if row["Low"] < p_sellside_liquidity and i.time() < tp1_close.time(): # check for dips
        # print("Dip", row["Low"], i)
        dips.append(i)
    if row["High"] > p_buyside_liquidity and i.time() < tp1_close.time():
        # print("Above", row["High"], i)
        breaches.append(i)

# check swings
swing_high = []
for num, dip_t in enumerate(dips):
    print("Dip", dip_t)
    for i, row in data5min.iterrows():
        if i.time() < tp1_close.time() and i.time() > dip_t.time():
            if data5min["High"][i] > data5min["High"][i - timedelta(minutes=5)] and data5min["High"][i] > data5min["High"][i + timedelta(minutes=5)]:
                swing_high.append(i)

swing_low = []
for num, breach_t in enumerate(breaches):
    print("Breach", breach_t)
    for i, row in data5min.iterrows():
        if i.time() < tp1_close.time() and i.time() > dip_t.time():
            if data5min["Low"][i] < data5min["High"][i - timedelta(minutes=5)] and data5min["Low"][i] < data5min["High"][i + timedelta(minutes=5)]:
                swing_low.append(i)

p_swing_high = swing_high[0] # take first swing
print(p_swing_high)

green_fvg = []
for i, row in data5min.iterrows():
    if i.time() < tp1_close.time() and i.time() > tp1_open.time() and i.time() > p_swing_high.time():
        if data5min["High"][i - timedelta(minutes=5)] < data5min["Low"][i + timedelta(minutes=5)]:
            green_fvg.append([i, data5min["High"][i - timedelta(minutes=5)], data5min["Low"][i + timedelta(minutes=5)]])

p_green_fvg = green_fvg[0]

entry = p_green_fvg[2]
possible_entry_time = p_green_fvg[0] + timedelta(minutes=10)
print(entry)
print(possible_entry_time)
