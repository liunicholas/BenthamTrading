from __future__ import print_function
import numpy as np
import pandas as pd
import yfinance as yf
import trading_clock as tc
from datetime import datetime, date, time, timedelta
from time import sleep
from silver_bullet import *
import pytz
import os

def get_data(current_time):
    current_date = current_time.date()

    if not tc.OVERRIDE:
        data = {"twoDayAgoData": yf.download(progress=False, tickers=security, start=tc.get_delta_trading_date(security, current_date, -2), end=tc.get_delta_trading_date(security, current_date, -1), interval=f'{tc.INTERVAL}m'),
            "oneDayAgoData": yf.download(progress=False, tickers=security, start=tc.get_delta_trading_date(security, current_date, -1), end=current_date, interval=f'{tc.INTERVAL}m'),
            "todaysData": yf.download(progress=False, tickers=security, start=current_date, end=tc.get_delta_trading_date(security, current_date, 1), interval=f'{tc.INTERVAL}m')
            }
    else:
        data = {"twoDayAgoData": yf.download(progress=False, tickers=security, start=tc.get_delta_trading_date(security, current_date, -2), end=tc.get_delta_trading_date(security, current_date, -1), interval=f'{tc.INTERVAL}m'),
        "oneDayAgoData": yf.download(progress=False, tickers=security, start=tc.get_delta_trading_date(security, current_date, -1), end=current_date, interval=f'{tc.INTERVAL}m'),
        "todaysData": yf.download(progress=False, tickers=security, start=current_date, end=tc.get_delta_trading_date(security, current_date, 1), interval=f'{tc.INTERVAL}m')
        }
     
        temp = []
        for i, row in data["todaysData"].iterrows():
            if i+timedelta(minutes=tc.INTERVAL) <= tc.OVERRIDE_TIME:
                temp.append(row)

        if temp:
            data["todaysData"] = pd.concat(temp, axis=1).T
        else:
            data["todaysData"] = pd.DataFrame()

    return data

def get_previous_day_swings(current_time=tc.get_today()):
    # print("CT", current_time)
    takeProfitSwingLows, takeProfitSwingHighs = [], []
    yesterdata = get_data(current_time)["oneDayAgoData"]

    for i in yesterdata.index[:-2]:
        threeCandles = yesterdata[i:i+timedelta(minutes=tc.INTERVAL*2)]
        middleCandle = threeCandles[-2:-1]
        middleCandleTime = middleCandle.index.item()

        if Swing.isSwingHigh(threeCandles):
            swing = Swing(middleCandleTime, middleCandle["High"][-1], "HIGH")
            takeProfitSwingHighs.append(swing)

        if Swing.isSwingLow(threeCandles):
            swing = Swing(middleCandleTime, middleCandle["Low"][-1], "LOW")
            takeProfitSwingLows.append(swing)
    
    return takeProfitSwingLows, takeProfitSwingHighs

def run_cycle(current_time, last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs):
    data = get_data(current_time)
    sleep(0)
    # print(data["todaysData"])

    # only iterate through procedure on new data
    if ((last_known_data_point is None) or (last_known_data_point < data["todaysData"].index[-1])) and (not data["todaysData"].empty):

        # iterate through liquidity lines
        for liquidity_line in liquidity_lines:
            # print(data["todaysData"].iloc[-1])
            liquidity_line.breach_list.append(data["todaysData"][-1:])

            # iterate through breaches in each liquidity line if swings can form
            if len(data["todaysData"]) >= 3:
                middleCandleTime = data["todaysData"].index[-2]

                for breach in liquidity_line.breach_list:
                    breach.swing_list.append(data["todaysData"][-3:])

                    # iterate through swings in each breach
                    for swing in breach.swing_list:
                        swing.FVG_list.append(data["todaysData"][-3:])

                        # iterate through FVGs in each swing
                        for FVG in swing.FVG_list:
                            candidate_trades.append(
                                FVG, takeProfitSwingLows, takeProfitSwingHighs)

        last_known_data_point = data["todaysData"].index[-1]

    # separate function for take profit points
    if len(data["todaysData"]) >= 3:
        middleCandleTime = data["todaysData"].index[-2]
        if Swing.isSwingHigh(data["todaysData"][-3:]):
            swingHigh = Swing(
                middleCandleTime, data["todaysData"].iloc[-2]["High"], "HIGH")
            takeProfitSwingHighs.append(swingHigh)

        if Swing.isSwingLow(data["todaysData"][-3:]):
            swingLow = Swing(
                middleCandleTime, data["todaysData"].iloc[-2]["Low"], "LOW")
            takeProfitSwingLows.append(swingLow)

    return last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs

def managePortfolio(candidate_trades):
    pass
    
def run_day(CATCH_UP):
    takeProfitSwingLows, takeProfitSwingHighs = get_previous_day_swings()

    liquidity_lines = get_primary_liquidity()
    candidate_trades = CandidateTrades()
    last_known_data_point = None

    if CATCH_UP:
        start = tc.localize(datetime.combine(
            tc.get_today().date(), tc.exchange_openclose[security][0]))
        end = datetime.now(tc.new_york_tz)
        this_generator = tc.get_generator([start,end])

        for simulated_time in this_generator:
            tc.override(simulated_time)
            current_time = tc.get_today()
            last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs = run_cycle(current_time, last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs)

            if not os.path.exists(f"logs/candidate_trades_{tc.get_today().date()}.txt"):
                with open(f"logs/candidate_trades_{tc.get_today().date()}.txt", "w") as f:
                    f.write("Proprietary Information of Bentham Trading ")

        tc.turn_off_override()

    else:
        with open(f"logs/candidate_trades_{tc.get_today().date()}.txt", "w") as f:
            f.write("Proprietary Information of Bentham Trading ")                                                                                                                
    
    while tc.is_market_open(security):
        current_time = tc.get_today()
        last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs = run_cycle(current_time, last_known_data_point, liquidity_lines,
                  candidate_trades, takeProfitSwingLows, takeProfitSwingHighs)
        
        # check on portfolio every iteration
        managePortfolio(candidate_trades)

    return

def main():
    LIVE = True
    PRINTED_MARKET_CLOSED = False
    while LIVE:
        if tc.is_market_open(security):
            PRINTED_MARKET_CLOSED = False

            CATCH_UP = False
            if tc.get_today() > tc.localize(datetime.combine(tc.get_today().date(), tc.exchange_openclose[security][0])):
                CATCH_UP = True
                
            run_day(CATCH_UP)
        else:
            if not PRINTED_MARKET_CLOSED:
                print("MARKET CLOSED")
                PRINTED_MARKET_CLOSED = True

if __name__ == "__main__":
    main()