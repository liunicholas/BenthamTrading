import numpy as np
import pandas as pd
import yfinance as yf
import trading_clock
from datetime import datetime, time, timedelta, date
import util


def get_primary_liquidity():
    current_time = datetime.now(trading_clock.new_york_tz)
    dataForLiquidity = yf.download(tickers='^spx', start=current_time.date() - timedelta(days=1), end=current_time.date(), interval='1d')

    pSellsideLiquidity = dataForLiquidity.loc[:, "Low"][0]
    pBuysideLiquidity = dataForLiquidity.loc[:, "High"][0]
    print(f"buyside liquidity: {pBuysideLiquidity}")
    print(f"sellside liquidity: {pSellsideLiquidity}")
    
    return pBuysideLiquidity, pSellsideLiquidity

def get_data(current_time):
    data = {"twoDayAgoData": yf.download(tickers='^spx', start=current_time.date() - timedelta(days=2), end=current_time.date() - timedelta(days=1), interval='5m'),
        "oneDayAgoData": yf.download(tickers='^spx', start=current_time.date() - timedelta(days=1), end=current_time.date(), interval='5m'),
        "todaysData": yf.download(tickers='^spx', start=current_time.date(), end=current_time.date() + timedelta(days=1), interval='5m')
        }

    return data

def get_buyside_sellside_breaches(data, pBuysideLiquidity, pSellsideLiquidity):
    sellside_breaches = {}
    buyside_breaches = {}
    todaysData = data["todaysData"]

    for i, row in todaysData.iterrows():
        if row["Low"] < pSellsideLiquidity:
            print(f"primary sellside liquidity breached at {i} at {row['Low']}")
            sellside_breaches[i] = row['Low']
        if row["High"] > pBuysideLiquidity:
            print(f"primary buyside liquidity breached at {i} at {row['High']}")
            buyside_breaches[i] = row['High']

    return sellside_breaches, buyside_breaches

def get_swing_lows(data):
    swingLows = {}
    dataForSwings = pd.concat(data["oneDayAgoData"],data["todaysData"])
    for i, row in dataForSwings.iloc[:-2].iterrows():
        preTime = i
        currTime = i + timedelta(minutes=5)
        postTime = i + timedelta(minutes=10)
        # check for swing low
        if dataForSwings.loc[currTime, "Low"] < dataForSwings.loc[preTime, "Low"] and dataForSwings.loc[currTime, "Low"] < dataForSwings.loc[postTime, "Low"]:
            print(f"swing low at {currTime} at {dataForSwings.loc[currTime, 'Low']}")
            swingLows[i] = dataForSwings.loc[currTime, 'Low']
    
    return swingLows

def get_swing_highs(data):
    swingHighs = {}
    dataForSwings = pd.concat(data["oneDayAgoData"], data["todaysData"])
    for i, row in dataForSwings.iloc[:-2].iterrows():
        preTime = i
        currTime = i + timedelta(minutes=5)
        postTime = i + timedelta(minutes=10)
        # check for swing low
        if dataForSwings.loc[currTime, "Low"] < dataForSwings.loc[preTime, "Low"] and dataForSwings.loc[currTime, "Low"] < dataForSwings.loc[postTime, "Low"]:
            print(
                f"swing low at {currTime} at {dataForSwings.loc[currTime, 'Low']}")
            swingHighs[i] = dataForSwings.loc[currTime, 'Low']

    return swingHighs

def search_green_fvg(swing_highs, data):
    # between 10-11 after swing high

    p_swing_high = swing_highs[0]
    todaysData = data["todaysData"]
    
    green_fvgs = {}
    for i, row in todaysData.iloc[2:].iterrows():
        timeLeft = i - timedelta(minutes=10)
        timeMid = i - timedelta(minutes=5)
        timeRight = i
        
        if trading_clock.datetime_is_between(timeRight, "10:00", "11:00") and timeLeft >= p_swing_high:
            if todaysData["High"][timeLeft] < todaysData["Low"][timeRight]:
    
                green_fvgs[timeRight] = {"entry":todaysData["Low"][timeRight], "stop":todaysData["High"][timeLeft]}

    return green_fvgs


def search_red_fvg(swing_lows, data):
    # between 10-11 after swing low

    p_swing_low = swing_lows[0]
    todaysData = data["todaysData"]

    red_fvgs = {}
    for i, row in todaysData.iloc[2:].iterrows():
        timeLeft = i - timedelta(minutes=10)
        timeMid = i - timedelta(minutes=5)
        timeRight = i

        if trading_clock.datetime_is_between(timeRight, "10:00", "11:00") and timeLeft >= p_swing_low:
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
                        takeProfitPrice = swing_highs[potential]
                        takeProfitTime = potential

            if takeProfitPrice != float("inf"):
                positionSize = 250 / ((stopLimit-entryPrice)*10)

                tradeOrder = util.TradeOrder(fvg, entryPrice, stopLimit, takeProfitPrice, positionSize)
                candidateTrades.append(tradeOrder)

    if green_FVGs:
        for fvg in green_FVGs:
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

                tradeOrder = util.TradeOrder(fvg, entryPrice, stopLimit, takeProfitPrice, positionSize)
                candidateTrades.append(tradeOrder)
    
    return candidateTrades

def managePortfolio():
    pass
    
def run_day():
    primary_buyside_liquidity, primary_sellside_liquidity = get_primary_liquidity()
    
    while trading_clock.is_market_open("^SPX"):
        current_time = datetime.now(trading_clock.new_york_tz)
        data = get_data(current_time)
        
        if trading_clock.datetime_is_between(current_time, "10:00", "11:00"): #AM Session
            sellside_breaches, buyside_breaches = get_buyside_sellside_breaches(data)
            CHECK_GREEN_FVG = False
            CHECK_RED_FVG = False

            if sellside_breaches:
                swing_lows = get_swing_lows(data)
                for breach in sellside_breaches:
                    if breach <= datetime.combine(current_time.date(), time(10,00,00)):
                        for swingLow in swing_lows:
                            if swingLow > breach:
                                CHECK_RED_FVG = True
            
            if buyside_breaches:
                swing_highs = get_swing_lows(data)
                for breach in buyside_breaches:
                    if breach <= datetime.combine(current_time.date(), time(10, 00, 00)):
                        for swingHigh in swing_highs:
                            if swingHigh > breach:
                                CHECK_GREEN_FVG = True
            
            red_FVGs = {}
            green_FVGs = {}

            if CHECK_RED_FVG:
                red_FVGs = search_red_fvg(swing_lows, data)
                # if red_FVGs:
            
            if CHECK_GREEN_FVG:
                green_FVGs = search_green_fvg(swing_highs, data)
                # if green_FVGs:
            
            # entry, stop limit, take profit, position size
            candidateTrades = find_candidate_trades(red_FVGs, green_FVGs, swing_highs, swing_lows)
            
            with open(f"logs/candidate_trades_{current_time.date()}_AM.txt") as f:
                f.write("Proprietary Information of Bentham Trading")
                f.write(current_time.date())
                for candidate in candidateTrades:
                    f.write(str(candidateTrades))
            
        if trading_clock.datetime_is_between(current_time, "14:00", "15:00"): #PM Session
            sellside_breaches, buyside_breaches = get_buyside_sellside_breaches(data)
            CHECK_GREEN_FVG = False
            CHECK_RED_FVG = False

            if sellside_breaches:
                swing_lows = get_swing_lows(data)
                for breach in sellside_breaches:
                    if breach <= datetime.combine(current_time.date(), time(14, 00, 00)):
                        for swingLow in swing_lows:
                            if swingLow > breach:
                                CHECK_RED_FVG = True

            if buyside_breaches:
                swing_highs = get_swing_lows(data)
                for breach in buyside_breaches:
                    if breach <= datetime.combine(current_time.date(), time(14, 00, 00)):
                        for swingHigh in swing_highs:
                            if swingHigh > breach:
                                CHECK_GREEN_FVG = True

            red_FVGs = {}
            green_FVGs = {}

            if CHECK_RED_FVG:
                red_FVGs = search_red_fvg(swing_lows, data)
                # if red_FVGs:

            if CHECK_GREEN_FVG:
                green_FVGs = search_green_fvg(swing_highs, data)
                # if green_FVGs:

            # entry, stop limit, take profit, position size
            candidateTrades = find_candidate_trades(
                red_FVGs, green_FVGs, swing_highs, swing_lows)

            with open(f"logs/candidate_trades_{current_time.date()}_PM.txt") as f:
                f.write("Proprietary Information of Bentham Trading")
                f.write(current_time.date())
                for candidate in candidateTrades:
                    f.write(str(candidateTrades))
        
        managePortfolio(candidateTrades)

    return

if __name__ == "__main__":
    LIVE = True
    # derivative = "^SPX"
    PRINTED_MARKET_CLOSED = False
    while LIVE:
        if trading_clock.is_market_open("^SPX"):
            PRINTED_MARKET_CLOSED = False
            run_day()
        else:
            if not PRINTED_MARKET_CLOSED:
                print("MARKET CLOSED")
                PRINTED_MARKET_CLOSED = True
