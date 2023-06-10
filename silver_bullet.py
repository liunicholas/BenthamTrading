import numpy as np
import pandas as pd
import yfinance as yf
import trading_clock
from datetime import datetime, time, timedelta, date
import util
import pytz

security = "^spx"

def get_primary_liquidity():
    current_time = trading_clock.get_today()
    dataForLiquidity = yf.download(tickers=security, start=current_time.date() - timedelta(days=1), end=current_time.date(), interval='1d')

    pSellsideLiquidity = dataForLiquidity["Low"][0]
    pBuysideLiquidity = dataForLiquidity["High"][0]
    print(f"buyside liquidity: {pBuysideLiquidity}")
    print(f"sellside liquidity: {pSellsideLiquidity}")
    
    return pBuysideLiquidity, pSellsideLiquidity

def get_data(current_time):
    data = {"twoDayAgoData": yf.download(tickers=security, start=current_time.date() - timedelta(days=2), end=current_time.date() - timedelta(days=1), interval='5m'),
        "oneDayAgoData": yf.download(tickers=security, start=current_time.date() - timedelta(days=1), end=current_time.date(), interval='5m'),
        "todaysData": yf.download(tickers=security, start=current_time.date(), end=current_time.date() + timedelta(days=1), interval='5m')
        }

    return data

def get_buyside_sellside_breaches(data, pBuysideLiquidity, pSellsideLiquidity):
    sellside_breaches = {}
    buyside_breaches = {}
    todaysData = data["todaysData"]

    for i, row in todaysData.iterrows():
        if row["Low"] <= pSellsideLiquidity:
            print(f"primary sellside liquidity breached at {i} at {row['Low']}")
            sellside_breaches[i] = row['Low']
        if row["High"] >= pBuysideLiquidity:
            print(f"primary buyside liquidity breached at {i} at {row['High']}")
            buyside_breaches[i] = row['High']

    return sellside_breaches, buyside_breaches

def get_swing_lows(data):
    swingLows = {}

    def swingLowHelper(dayData):
        for i, row in dayData.iloc[2:].iterrows():
            timeLeft = i - timedelta(minutes=10)
            timeMid = i - timedelta(minutes=5)
            timeRight = i
            # check for swing low
            if dayData['Low'][timeMid] < dayData['Low'][timeLeft] and dayData['Low'][timeMid] < dayData['Low'][timeRight]:
                print(f"swing low at {timeMid} at {dayData['Low'][timeMid]}")
                swingLows[timeMid] = dayData['Low'][timeMid]
    
    swingLowHelper(data["oneDayAgoData"])
    swingLowHelper(data["todaysData"])

    return swingLows

def get_swing_highs(data):
    swingHighs = {}

    def swingHighHelper(dayData):
        for i, row in dayData.iloc[2:].iterrows():
            timeLeft = i - timedelta(minutes=10)
            timeMid = i - timedelta(minutes=5)
            timeRight = i
            # check for swing low
            if dayData['High'][timeMid] > dayData['High'][timeLeft] and dayData['High'][timeMid] > dayData['High'][timeRight]:
                print(f"swing high at {timeMid} at {dayData['High'][timeMid]}")
                swingHighs[timeMid] = dayData['High'][timeMid]

    swingHighHelper(data["oneDayAgoData"])
    swingHighHelper(data["todaysData"])

    return swingHighs

def search_green_fvg(swing_highs, data, openTime, closeTime):
    p_swing_high = next(iter(swing_highs.items()))[0]  # get the time
    todaysData = data["todaysData"]
    
    green_fvgs = {}
    for i, row in todaysData.iloc[2:].iterrows():
        timeLeft = i - timedelta(minutes=10)
        timeMid = i - timedelta(minutes=5)
        timeRight = i
        
        if trading_clock.datetime_is_between(timeRight, openTime, closeTime) and timeLeft >= p_swing_high:
            if todaysData["High"][timeLeft] < todaysData["Low"][timeRight]:
    
                green_fvgs[timeRight] = {"entry":todaysData["Low"][timeRight], "stop":todaysData["High"][timeLeft]}

    return green_fvgs

def search_red_fvg(swing_lows, data, openTime, closeTime):
    p_swing_low = next(iter(swing_lows.items()))[0] # get the time
    todaysData = data["todaysData"]

    red_fvgs = {}
    for i, row in todaysData.iloc[2:].iterrows():
        timeLeft = i - timedelta(minutes=10)
        timeMid = i - timedelta(minutes=5)
        timeRight = i

        if trading_clock.datetime_is_between(timeRight, openTime, closeTime) and timeLeft >= p_swing_low:
            if todaysData["Low"][timeLeft] > todaysData["High"][timeRight]:
                red_fvgs[timeRight] = {"entry": todaysData["High"][timeRight], "stop": todaysData["Low"][timeLeft]}

    return red_fvgs

def find_candidate_trades(red_FVGs, green_FVGs, swing_highs, swing_lows):
    candidateTrades = []

    if red_FVGs:
        for fvg in red_FVGs:
            FVGtime = fvg + timedelta(minutes=5)
            entryPrice = red_FVGs[fvg]["entry"]
            stopLimit = red_FVGs[fvg]["stop"]

            pSwingThreshold = entryPrice - 10

            takeProfitPrice = float("inf")
            takeProfitTime = -1
            for potential in swing_lows:
                if potential < fvg and swing_lows[potential] < pSwingThreshold:
                    if pSwingThreshold-swing_lows[potential] < pSwingThreshold-takeProfitPrice:
                        takeProfitPrice = swing_lows[potential]
                        takeProfitTime = potential

            if takeProfitPrice != float("inf"):
                positionSize = 250 / ((stopLimit-entryPrice)*10)

                tradeOrder = util.TradeOrder(FVGtime, entryPrice, stopLimit, takeProfitPrice, positionSize)
                candidateTrades.append(tradeOrder)

    if green_FVGs:
        for fvg in green_FVGs:
            # print("here")
            FVGtime = fvg + timedelta(minutes=5)
            entryPrice = green_FVGs[fvg]["entry"]
            stopLimit = green_FVGs[fvg]["stop"]

            pSwingThreshold = entryPrice + 10

            takeProfitPrice = float("inf")
            takeProfitTime = -1
            for potential in swing_highs:
                if potential < fvg and swing_highs[potential] > pSwingThreshold:
                    if swing_highs[potential]-pSwingThreshold < takeProfitPrice-pSwingThreshold:
                        takeProfitPrice = swing_highs[potential]
                        takeProfitTime = potential
            
            if takeProfitPrice != float("inf"):
                positionSize = 250 / ((entryPrice-stopLimit)*10)

                tradeOrder = util.TradeOrder(FVGtime, entryPrice, stopLimit, takeProfitPrice, positionSize)
                candidateTrades.append(tradeOrder)
    
    return candidateTrades

def managePortfolio(candidateTrades):
    pass
    
def run_day():
    primary_buyside_liquidity, primary_sellside_liquidity = get_primary_liquidity()

    candidateTrades = []

    swing_lows = {}
    swing_highs = {}

    red_FVGs = {}
    green_FVGs = {}
    
    while trading_clock.is_market_open(security):
        current_time = trading_clock.get_today()
        data = get_data(current_time)
        
        if trading_clock.datetime_is_between(current_time, "10:00", "11:00"): #AM Session
            sellside_breaches, buyside_breaches = get_buyside_sellside_breaches(
                data, primary_buyside_liquidity, primary_sellside_liquidity)
            
            CHECK_GREEN_FVG = False
            CHECK_RED_FVG = False

            if buyside_breaches:
                swing_lows = get_swing_lows(data)
                tempSwingLows = {}
                for breach in buyside_breaches:
                    current_time.date() + timedelta(hour=10)
                    if breach <= trading_clock.time_during_day(current_time, "10:00"):
                        for swingLow in swing_lows:
                            if swingLow > breach:
                                CHECK_RED_FVG = True
                                if CHECK_RED_FVG:
                                    tempSwingLows[swingLow] = swing_lows[swingLow]
                
                swing_lows = tempSwingLows

                            # FILTER THIS SHIT OUT temp fixed
            
            if sellside_breaches:
                swing_highs = get_swing_highs(data)
                tempSwingHighs = {}
                for breach in sellside_breaches:
                    if breach <= trading_clock.time_during_day(current_time, "10:00"):
                        for swingHigh in swing_highs:
                            if swingHigh > breach:
                                CHECK_GREEN_FVG = True
                                if CHECK_GREEN_FVG:
                                    tempSwingHighs[swingHigh] = swing_highs[swingHigh]

                swing_highs = tempSwingHighs

            if CHECK_RED_FVG:
                red_FVGs = search_red_fvg(swing_lows, data, "10:00", "11:00")
            
            if CHECK_GREEN_FVG:
                green_FVGs = search_green_fvg(swing_highs, data, "10:00", "11:00")
            
            # entry, stop limit, take profit, position size
            candidateTrades = find_candidate_trades(red_FVGs, green_FVGs, swing_highs, swing_lows)
            
            with open(f"logs/candidate_trades_{current_time.date()}_AM.txt", "w") as f:
                f.write("Proprietary Information of Bentham Trading ")
                f.write(current_time.date().strftime("%Y-%m-%d"))
                f.write("\n")
                for candidate in candidateTrades:
                    f.write(str(candidate))
            
        if trading_clock.datetime_is_between(current_time, "14:00", "15:00"): #PM Session
            sellside_breaches, buyside_breaches = get_buyside_sellside_breaches(
                data, primary_buyside_liquidity, primary_sellside_liquidity)
            
            CHECK_GREEN_FVG = False
            CHECK_RED_FVG = False

            if sellside_breaches:
                swing_lows = get_swing_lows(data)
                for breach in sellside_breaches:
                    if breach <= datetime.combine(current_time.date(), time(14, 00, 00)).astimezone(trading_clock.new_york_tz):
                        for swingLow in swing_lows:
                            if swingLow > breach:
                                CHECK_RED_FVG = True

            if buyside_breaches:
                swing_highs = get_swing_lows(data)
                for breach in buyside_breaches:
                    if breach <= datetime.combine(current_time.date(), time(14, 00, 00)).astimezone(trading_clock.new_york_tz):
                        for swingHigh in swing_highs:
                            if swingHigh > breach:
                                CHECK_GREEN_FVG = True

            if CHECK_RED_FVG:
                red_FVGs = search_red_fvg(swing_lows, data, "14:00", "15:00")

            if CHECK_GREEN_FVG:
                green_FVGs = search_green_fvg(swing_highs, data, "14:00", "15:00")

            # entry, stop limit, take profit, position size
            candidateTrades = find_candidate_trades(
                red_FVGs, green_FVGs, swing_highs, swing_lows)

            with open(f"logs/candidate_trades_{current_time.date()}_PM.txt", "w") as f:
                f.write("Proprietary Information of Bentham Trading")
                f.write(current_time.date().strftime("%Y-%m-%d"))
                f.write("\n")
                for candidate in candidateTrades:
                    f.write(str(candidate))
        
        managePortfolio(candidateTrades)

    return

if __name__ == "__main__":
    LIVE = True
    PRINTED_MARKET_CLOSED = False
    while LIVE:
        if trading_clock.is_market_open(security):
            PRINTED_MARKET_CLOSED = False
            run_day()
        else:
            if not PRINTED_MARKET_CLOSED:
                print("MARKET CLOSED")
                PRINTED_MARKET_CLOSED = True
