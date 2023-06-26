import numpy as np
import pandas as pd
import trading_clock as tc
from data import *
from datetime import date

def get_FVGS(security, ts_data, odds_date):
    # key is date distance, value is mid price level
    FVGS = {}

    left_date, left_low, left_high = ts_data.index[0], ts_data["Low"][0], ts_data["High"][0]
    middle_date, middle_low, middle_high = ts_data.index[1], ts_data["Low"][1], ts_data["High"][1]
    for right_date, right_low, right_high in zip(ts_data.index[2:], ts_data["Low"][2:], ts_data["High"][2:]):
        
        timedelta = tc.get_trading_days_between(security, right_date.to_pydatetime().date(), odds_date)

        if right_low > left_high:
            FVGS[timedelta] = (right_low+left_high)/2
        if right_high < left_low:
            FVGS[timedelta] = (right_high+left_low)/2

        left_date, left_low, left_high = middle_date, middle_low, middle_high
        middle_date, middle_low, middle_high = right_date, right_low, right_high
    
    return FVGS

def get_SWINGS(security, ts_data, odds_date):
    SWINGS = {}

    left_date, left_low, left_high = ts_data.index[0], ts_data["Low"][0], ts_data["High"][0]
    middle_date, middle_low, middle_high = ts_data.index[1], ts_data["Low"][1], ts_data["High"][1]
    for right_date, right_low, right_high in zip(ts_data.index[2:], ts_data["Low"][2:], ts_data["High"][2:]):

        timedelta = tc.get_trading_days_between(
            security, middle_date.to_pydatetime().date(), odds_date)

        if middle_high > right_high and middle_high > left_high:
            SWINGS[timedelta] = middle_high
        if middle_low < right_low and middle_low < left_low:
            SWINGS[timedelta] = middle_low

        left_date, left_low, left_high = middle_date, middle_low, middle_high
        middle_date, middle_low, middle_high = right_date, right_low, right_high

    return SWINGS
    
def get_coin_odds(odds_date, security):
    security_data = SecurityData(security)
    # one month dailies
    security_data.get_yfinance_data(
        odds_date-timedelta(weeks=4), odds_date, interval="1d", name="dailies")
    # one year weeklies
    security_data.get_yfinance_data(
        odds_date-timedelta(weeks=52), odds_date, interval="1wk", name="weeklies")

    # get all midpoints of FVGS and their time distance from odds date
    daily_FVGS = get_FVGS(security, security_data["dailies"], odds_date)
    # print(daily_FVGS)
    weekly_FVGS = get_FVGS(security, security_data["weeklies"], odds_date)
    # print(weekly_FVGS)

    # get all swings and their time distance from odds date
    daily_SWINGS = get_SWINGS(security, security_data["dailies"], odds_date)
    # print(daily_SWINGS)
    weekly_SWINGS = get_SWINGS(security, security_data["dailies"], odds_date)
    # print(weekly_SWINGS)

    current_price = security_data["dailies"][-1:]["Close"].item()
    # print(current_price)

    heads_weight = 0
    tails_weight = 0

    for fvg in daily_FVGS:
        if current_price < daily_FVGS[fvg]:
            heads_weight += 8*((daily_FVGS[fvg]-current_price) * (20-fvg))**(1/2)
        if current_price > daily_FVGS[fvg]:
            tails_weight += 8*((current_price-daily_FVGS[fvg]) * (20-fvg))**(1/2)
    
    for fvg in weekly_FVGS:
        if current_price < weekly_FVGS[fvg]:
            heads_weight += 2*((weekly_FVGS[fvg]-current_price) * (252-fvg))**(1/2)
        if current_price > weekly_FVGS[fvg]:
            tails_weight += 2*((current_price-weekly_FVGS[fvg]) * (252-fvg))**(1/2)
    
    for swing in daily_SWINGS:
        if current_price < daily_SWINGS[swing]:
            heads_weight += 2*((daily_SWINGS[swing] -
                             current_price) * (20-swing))**(1/4)
        if current_price > daily_SWINGS[swing]:
            tails_weight += 2*((current_price -
                             daily_SWINGS[swing]) * (20-swing))**(1/4)

    for swing in weekly_SWINGS:
        if current_price < weekly_SWINGS[swing]:
            heads_weight += 1*((weekly_SWINGS[swing] -
                             current_price) * (252-swing))**(1/4)
        if current_price > weekly_SWINGS[swing]:
            tails_weight += 1*((current_price -
                             weekly_SWINGS[swing]) * (252-swing))**(1/4)

    heads_odds = heads_weight / (heads_weight+tails_weight)
    tails_odd = tails_weight / (heads_weight+tails_weight)
    return heads_odds, tails_odd

if __name__ == "__main__":
    security = "^spx"
    odds_date = date(2023, 5, 12)
    for i in range(35):
        heads_odd, tails_odd = get_coin_odds(odds_date + timedelta(days=i), security)
        print(f"Odds for {odds_date + timedelta(days=i)}")
        print(f"Bull: {heads_odd:0.2f}")
        print(f"Bear: {tails_odd:0.2f}")
