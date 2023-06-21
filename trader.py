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

def run_cycle(data, current_time, last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs):
    print(f"[INFO] Cycle run at {current_time}")

    # print(data["todaysData"].tail())
    print(data["todaysData"])

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
    with open(f"trade_logs/candidate_trades_{tc.get_today().date()}.txt", "w") as f:
        f.write("Proprietary Information of Bentham Trading \n")

    spx_data = SecurityData(security=security)
    spx_data.get_day_data("yesterdata", tc.get_today(), interval=INTERVAL, delta=-1)
    takeProfitSwingLows, takeProfitSwingHighs = get_previous_day_swings(spx_data["yesterdata"])

    liquidity_lines = get_primary_liquidity(current_time=tc.get_today())
    GOT_SECONDARY_LIQUIDITY = False

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

            if (current_time.minute % INTERVAL) == 0:  
                spx_data.get_day_data("todaysData", current_time, interval=INTERVAL, delta=0)
            
            if tc.datetime_is_between(current_time, "11:00", "11:05") and not GOT_SECONDARY_LIQUIDITY:
                print("ADDING LIQUIDITY LINES")
                liquidity_lines += get_secondary_liquidity(current_time, spx_data["todaysData"])
                GOT_SECONDARY_LIQUIDITY = True

            last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs = run_cycle(
                spx_data, current_time, last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs)

        tc.turn_off_override()                                                                                                          
    
    last_known_minute = last_known_data_point.minute
    while tc.is_market_open(security, current=tc.get_today()):
        current_time = tc.get_today()
        if current_time.second >=0 and current_time.second <= 5 and current_time.minute != last_known_minute:
            last_known_minute = current_time.minute
            spx_data.get_day_data("todaysData", current_time, interval=INTERVAL, delta=0)

            if tc.datetime_is_between(current_time, "11:00", "11:05") and not GOT_SECONDARY_LIQUIDITY:
                print("ADDING LIQUIDITY LINES")
                liquidity_lines += get_secondary_liquidity(current_time, spx_data["todaysData"])
                GOT_SECONDARY_LIQUIDITY = True

            last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs = run_cycle(
                spx_data, current_time, last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs)
        
        # check on portfolio every iteration
        managePortfolio(candidate_trades)

    return

def main():
    LIVE = True
    last_known_minute = None
    while LIVE:
        current_time = tc.get_today()
        if (last_known_minute is None) or (current_time.second >= 0 and current_time.second <= 5 and current_time.minute != last_known_minute):
            last_known_minute = current_time.minute
            print(f"[INFO] Checking market open at {current_time}")

            if tc.is_market_open(security, current_time, VERBOSE=True):
                print("MARKET OPENED")

                CATCH_UP = False
                if tc.get_today()+timedelta(INTERVAL) > tc.localize(datetime.combine(tc.get_today().date(), tc.exchange_openclose[security][0])):
                    CATCH_UP = True
                    
                run_day(CATCH_UP)
            else:
                print("MARKET CLOSED")


if __name__ == "__main__":
    main()