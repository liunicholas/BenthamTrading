from __future__ import print_function
import numpy as np
import pandas as pd
import yfinance as yf
import trading_clock as tc
from data import *
from datetime import datetime, date, time, timedelta
from time import sleep
from silver_bullet import *
import os


def get_previous_day_swings(yesterdata):
    # print("CT", current_time)
    takeProfitSwingLows, takeProfitSwingHighs = [], []

    for i in yesterdata.index[:-2]:
        threeCandles = yesterdata[i:i+timedelta(minutes=INTERVAL*2)]
        middleCandle = threeCandles[-2:-1]
        middleCandleTime = middleCandle.index.item()

        if Swing.isSwingHigh(threeCandles):
            swing = Swing(middleCandleTime, middleCandle["High"][-1], "HIGH")
            takeProfitSwingHighs.append(swing)

        if Swing.isSwingLow(threeCandles):
            swing = Swing(middleCandleTime, middleCandle["Low"][-1], "LOW")
            takeProfitSwingLows.append(swing)
    
    return takeProfitSwingLows, takeProfitSwingHighs

def run_cycle(data, current_time, last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs):
    print(f"[INFO] Cycle run at {current_time}")
    print(data["todaysData"].tail())
    # only iterate through procedure on new data
    if ((last_known_data_point is None) or (last_known_data_point < data["todaysData"].index[-1])) and (not data["todaysData"].empty):
        # if tc.OVERRIDE == False:
        #     print(f"Live data pulled at {data['todaysData'].index[-1]}")
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
    spx_data = SecurityData(security=security)
    spx_data.get_day_data("yesterdata", tc.get_today(), interval=INTERVAL, delta=-1)
    takeProfitSwingLows, takeProfitSwingHighs = get_previous_day_swings(spx_data["yesterdata"])

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

            if (current_time.minute % 5) == 0:  
                spx_data.get_day_data("todaysData", current_time, interval=INTERVAL, delta=0)

            last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs = run_cycle(
                spx_data, current_time, last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs)

            if not os.path.exists(f"logs/candidate_trades_{tc.get_today().date()}.txt"):
                with open(f"logs/candidate_trades_{tc.get_today().date()}.txt", "w") as f:
                    f.write("Proprietary Information of Bentham Trading ")

        tc.turn_off_override()

    else:
        with open(f"logs/candidate_trades_{tc.get_today().date()}.txt", "w") as f:
            f.write("Proprietary Information of Bentham Trading ")                                                                                                                
    
    last_known_minute = last_known_data_point.minute
    while tc.is_market_open(security, current=tc.get_today()):
        current_time = tc.get_today()
        if current_time.second >=0 and current_time.second <= 5 and current_time.minute != last_known_minute:
            last_known_minute = current_time.minute

            spx_data.get_day_data("todaysData", current_time, interval=INTERVAL, delta=0)
    
            last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs = run_cycle(
                spx_data, current_time, last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs)
        
        # check on portfolio every iteration
        managePortfolio(candidate_trades)

    return

def main():
    LIVE = True
    # PRINTED_MARKET_CLOSED = False
    last_known_minute = None
    while LIVE:
        current_time = tc.get_today()
        # if last_known_minute is None:
        if (last_known_minute is None) or (current_time.second >= 0 and current_time.second <= 5 and current_time.minute != last_known_minute):
            last_known_minute = current_time.minute

            if tc.is_market_open(security, current_time, VERBOSE=True):
                # PRINTED_MARKET_CLOSED = False
                print("MARKET OPENED")

                CATCH_UP = False
                if tc.get_today()+timedelta(INTERVAL) > tc.localize(datetime.combine(tc.get_today().date(), tc.exchange_openclose[security][0])):
                    CATCH_UP = True
                    
                run_day(CATCH_UP)
            else:
                # if not PRINTED_MARKET_CLOSED:
                #     print("MARKET CLOSED")
                #     PRINTED_MARKET_CLOSED = True
                print("MARKET CLOSED")


if __name__ == "__main__":
    main()