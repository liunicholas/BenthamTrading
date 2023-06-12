from __future__ import print_function
import numpy as np
import pandas as pd
import yfinance as yf
import trading_clock as tc
from datetime import datetime, date, time, timedelta
from silver_bullet import *
import pytz

def get_data(current_time):
    current_date = current_time.date()

    if not tc.OVERRIDE:
        data = {"twoDayAgoData": yf.download(tickers=security, start=tc.get_delta_trading_date(security, current_date, -2), end=tc.get_delta_trading_date(security, current_date, -1), interval=f'{tc.INTERVAL}m'),
            "oneDayAgoData": yf.download(tickers=security, start=tc.get_delta_trading_date(security, current_date, -1), end=current_date, interval=f'{tc.INTERVAL}m'),
            "todaysData": yf.download(tickers=security, start=current_date, end=tc.get_delta_trading_date(security, current_date, 1), interval=f'{tc.INTERVAL}m')
            }
    else:
        data = {"twoDayAgoData": yf.download(tickers=security, start=tc.get_delta_trading_date(security, current_date, -2), end=tc.get_delta_trading_date(security, current_date, -1), interval=f'{tc.INTERVAL}m'),
        "oneDayAgoData": yf.download(tickers=security, start=tc.get_delta_trading_date(security, current_date, -1), end=current_date, interval=f'{tc.INTERVAL}m'),
        "todaysData": yf.download(tickers=security, start=current_date, end=tc.get_delta_trading_date(security, current_date, 1), interval=f'{tc.INTERVAL}m')
        }

        temp = []
        for i, row in data["todaysData"].iterrows():
            if i+timedelta(minutes=tc.INTERVAL) <= tc.OVERRIDE_TIME:
                temp.append(row)

        if temp:
            data["todaysData"] = pd.concat(temp, axis=1).T

    return data

def get_previous_day_swings(current_time=tc.get_today()):
    takeProfitSwingLows, takeProfitSwingHighs = [], []
    yesterdata = get_data(current_time)["oneDayAgoData"]

    for i in yesterdata.index[:-2]:
        threeCandles = yesterdata[i:i+timedelta(minutes=tc.INTERVAL*2)]
        middleCandle = threeCandles.iloc[-2]
        middleCandleTime = middleCandle.index

        if Swing.isSwingHigh(threeCandles):
            swing = Swing(middleCandleTime, middleCandle["High"], "HIGH")
            takeProfitSwingHighs.append(swing)

        if Swing.isSwingLow(threeCandles):
            swing = Swing(middleCandleTime, middleCandle["Low"], "LOW")
            takeProfitSwingLows.append(swing)
    
    return takeProfitSwingLows, takeProfitSwingHighs

def managePortfolio(candidate_trades):
    pass
    
def run_day(CATCH_UP):
    takeProfitSwingLows, takeProfitSwingHighs = get_previous_day_swings()

    liquidity_lines = LiquidityLine.get_primary_liquidity()
    candidate_trades = CandidateTrades()
    last_known_data_point = None

    if CATCH_UP:
        start = tc.exchange_openclose[security][0]
        end = datetime.now(tc.new_york_tz)
        this_generator = tc.get_generator([start,end])

        for simulated_time in this_generator:
            tc.override(simulated_time)
            current_time = simulated_time

    
    while tc.is_market_open(security):
        current_time = tc.get_today()
        data = get_data(current_time)
        
        # only iterate through procedure on new data
        if ((last_known_data_point is None) or (last_known_data_point != data["todaysData"].index[-1])) and (data["todaysData"]):

            # iterate through liquidity lines
            for liquidity_line in liquidity_lines:
                liquidity_line.breach_list.append(data["todaysData"][-1])
            
                # iterate through breaches in each liquidity line if swings can form
                if len(data["todaysData"]) >= 3:
                    middleCandleTime = data["todaysData"].index[-2]
                    
                    for breach in liquidity_line.breach_list:
                        breach.swing_list.append(data["todaysData"][-3:])
                        
                        for swing in breach.swing_list:
                            swing.FVG_list.append(data["todaysData"][-3:])
                        

        # separate function for take profit points
        if len(data["todaysData"]) >= 3:
            middleCandleTime = data["todaysData"].index[-2]
            if Swing.isSwingHigh(data["todaysData"][-3:]):
                swingHigh = Swing(middleCandleTime, data["todaysData"].iloc[-2]["todaysData"], "HIGH")
                takeProfitSwingHighs.append(swingHigh)
            
            if Swing.isSwingLow(data["todaysData"][-3:]):
                swingLow = Swing(middleCandleTime, data["todaysData"].iloc[-2]["todaysData"], "LOW")
                takeProfitSwingLows.append(swingLow)

            
        # find trades
        if tc.datetime_is_between(current_time, "10:00", "11:00"): #AM Session
            candidate_trades = find_candidate_trades(candidate_trades, liquidity_lines)
            
            # with open(f"logs/candidate_trades_{current_time.date()}_AM.txt", "w") as f:
            #     f.write("Proprietary Information of Bentham Trading ")
            #     f.write(current_time.date().strftime("%Y-%m-%d"))
            #     f.write("\n")
            #     for candidate in candidateTrades:
            #         f.write(str(candidate))
            
        if tc.datetime_is_between(current_time, "14:00", "15:00"): #PM Session
            candidateTrades = find_candidate_trades(candidate_trades, liquidity_lines)

            # with open(f"logs/candidate_trades_{current_time.date()}_PM.txt", "w") as f:
            #     f.write("Proprietary Information of Bentham Trading")
            #     f.write(current_time.date().strftime("%Y-%m-%d"))
            #     f.write("\n")
            #     for candidate in candidateTrades:
            #         f.write(str(candidate))
        
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
            if tc.get_today > tc.exchange_openclose[security][0]:
                CATCH_UP = True
                
            run_day(CATCH_UP)
        else:
            if not PRINTED_MARKET_CLOSED:
                print("MARKET CLOSED")
                PRINTED_MARKET_CLOSED = True
    

if __name__ == "__main__":
    main()