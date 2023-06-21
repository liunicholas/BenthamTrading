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

snp_ticker = "^spx"
ndq_ticker = "^ixic"

take_profit_margin = {snp_ticker: 10, ndq_ticker: 30}
stop_loss_margin = {snp_ticker: 3, ndq_ticker: 10}

def initialize_day(security):
    with open(f"trade_logs/{security}_candidate_trades_{tc.get_today().date()}.txt", "w") as f:
        f.write("Proprietary Information of Bentham Trading \n")

    security_data = SecurityData(security=security)
    security_data.get_day_data("yesterdata", tc.get_today(),
                          interval=INTERVAL, delta=-1)
    takeProfitSwingLows, takeProfitSwingHighs = get_previous_day_swings(
        security_data["yesterdata"])

    liquidity_lines = get_primary_liquidity(
        security, current_time=tc.get_today())
    GOT_SECONDARY_LIQUIDITY = False

    candidate_trades = CandidateTrades()
    last_known_data_point = None
    if tc.real_time()-timedelta(minutes=INTERVAL) > tc.localize(datetime.combine(tc.get_today().date(), tc.exchange_openclose[security][0])):
        start = tc.localize(datetime.combine(
            tc.get_today().date(), tc.exchange_openclose[security][0]))
        if tc.real_time() > tc.localize(datetime.combine(tc.get_today().date(), tc.exchange_openclose[security][1])):
            end = tc.localize(datetime.combine(
                tc.get_today().date(), tc.exchange_openclose[security][1]))
        else:
            end = tc.real_time()
        this_generator = tc.get_generator([start, end])

        for simulated_time in this_generator:
            tc.override(simulated_time)
            current_time = tc.get_today()

            if (current_time.minute % INTERVAL) == 0:
                security_data.get_day_data(
                    "todaysData", current_time, interval=INTERVAL, delta=0)

            if tc.datetime_is_between(current_time, "11:00", "11:05") and not GOT_SECONDARY_LIQUIDITY:
                print("ADDING LIQUIDITY LINES")
                liquidity_lines += get_secondary_liquidity(
                    security, current_time, security_data["todaysData"])
                GOT_SECONDARY_LIQUIDITY = True

            last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs = run_cycle(
                security, security_data, current_time, last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs)

        tc.turn_off_override()

    return last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs, security_data, GOT_SECONDARY_LIQUIDITY

def run_cycle(security, data, current_time, last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs):
    print(f"[INFO] Cycle run at {current_time}")

    print(data["todaysData"].tail())
    # print(data["todaysData"])

    # only iterate through procedure on new data
    if ((last_known_data_point is None) or (last_known_data_point < data["todaysData"].index[-1])) and (not data["todaysData"].empty):
        # if tc.OVERRIDE == False:
        #     print(f"Live data pulled at {data['todaysData'].index[-1]}")
        # iterate through liquidity lines
        for liquidity_line in liquidity_lines:
            # print(data["todaysData"].iloc[-1])
            liquidity_line.breach_list.append(
                security, data["todaysData"][-1:])

            # iterate through breaches in each liquidity line if swings can form
            if len(data["todaysData"]) >= 3:
                middleCandleTime = data["todaysData"].index[-2]

                for breach in liquidity_line.breach_list:
                    breach.swing_list.append(security, data["todaysData"][-3:])

                    # iterate through swings in each breach
                    for swing in breach.swing_list:
                        swing.FVG_list.append(
                            security, data["todaysData"][-3:])

                        # iterate through FVGs in each swing
                        for FVG in swing.FVG_list:
                            candidate_trades.append(
                                security, take_profit_margin[security], stop_loss_margin[security], FVG, takeProfitSwingLows, takeProfitSwingHighs)

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
    
def run_day():
    snp_last_known_data_point, snp_liquidity_lines, snp_candidate_trades, snp_takeProfitSwingLows, snp_takeProfitSwingHighs, snp_data, snp_GOT_SECONDARY_LIQUIDITY = \
        initialize_day(snp_ticker)
    
    ndq_last_known_data_point, ndq_liquidity_lines, ndq_candidate_trades, ndq_takeProfitSwingLows, ndq_takeProfitSwingHighs, ndq_data, ndq_GOT_SECONDARY_LIQUIDITY = \
        initialize_day(ndq_ticker)

    last_known_minute = -1
    while tc.is_market_open(snp_ticker, current=tc.get_today()):
        current_time = tc.get_today()
        if current_time.second >=0 and current_time.second <= 5 and current_time.minute != last_known_minute:
            last_known_minute = current_time.minute
            snp_data.get_day_data("todaysData", current_time, interval=INTERVAL, delta=0)
            ndq_data.get_day_data("todaysData", current_time, interval=INTERVAL, delta=0)

            if tc.datetime_is_between(current_time, "11:00", "11:05") and not snp_GOT_SECONDARY_LIQUIDITY:
                print("ADDING LIQUIDITY LINES")
                liquidity_lines += get_secondary_liquidity(
                    snp_ticker, current_time, snp_data["todaysData"])
                snp_GOT_SECONDARY_LIQUIDITY = True
            
            if tc.datetime_is_between(current_time, "11:00", "11:05") and not ndq_GOT_SECONDARY_LIQUIDITY:
                print("ADDING LIQUIDITY LINES")
                liquidity_lines += get_secondary_liquidity(
                    ndq_ticker, current_time, ndq_data["todaysData"])
                ndq_GOT_SECONDARY_LIQUIDITY = True

            snp_last_known_data_point, snp_liquidity_lines, snp_candidate_trades, snp_takeProfitSwingLows, snp_takeProfitSwingHighs = run_cycle(
                snp_ticker, snp_data, current_time, snp_last_known_data_point, snp_liquidity_lines, snp_candidate_trades, snp_takeProfitSwingLows, snp_takeProfitSwingHighs)

            ndq_last_known_data_point, ndq_liquidity_lines, ndq_candidate_trades, ndq_takeProfitSwingLows, ndq_takeProfitSwingHighs = run_cycle(
                ndq_ticker, ndq_data, current_time, ndq_last_known_data_point, ndq_liquidity_lines, ndq_candidate_trades, ndq_takeProfitSwingLows, ndq_takeProfitSwingHighs)
        
        # check on portfolio every iteration
        managePortfolio([snp_candidate_trades, ndq_candidate_trades])

    return

def main():
    LIVE = True
    last_known_minute = None
    while LIVE:
        # tc.override(tc.localize(datetime(year=2023, month=6, day=21,hour=16, minute=00)))
        current_time = tc.get_today()
        if (last_known_minute is None) or (current_time.second >= 0 and current_time.second <= 5 and current_time.minute != last_known_minute):
            last_known_minute = current_time.minute

            if tc.is_market_open(snp_ticker, current_time, VERBOSE=True):
                print("MARKET OPENED")
                run_day()

            else:
                print("MARKET CLOSED")


if __name__ == "__main__":
    main()