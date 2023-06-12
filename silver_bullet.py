from __future__ import print_function
import trading_clock as tc
import yfinance as yf
from datetime import datetime, date, time, timedelta

security = "^spx"
trading_period_1_open = "10:00"
trading_period_1_close = "11:00"
trading_period_2_open = "14:00"
trading_period_2_close = "15:00"
take_profit_margin = 10


class FVG:
    def __init__(self, time, entry, stop_loss, FVG_type):
        self.time = time
        self.entry = entry
        self.stop_loss = stop_loss
        self.FVG_type = FVG_type #"GREEN" "RED"

    def __str__(self):
        return f"FVG at time {self.time} at entry {self.entry} and stop loss {self.stop_loss}"

class FVGList:
    def __init__(self, swing, fl=[]):
        self.swing = swing
        self.FVG_list = fl
    
    def append(self, threeCandles):
        # FVG is during trading period 10-11, 14-15 DONE
        # After Swing High: Green FVG - 3rd low > 1st high, above swing high pl
        # After Swing Low: Red FVG - 3rd high < 1st low, below swing low pl

        leftCandle = threeCandles.iloc[0]
        middleCandle = threeCandles.iloc[1]
        rightCandle = threeCandles.iloc[2]

        if tc.datetime_is_between(leftCandle.index, trading_period_1_open, trading_period_1_close) or tc.datetime_is_between(leftCandle.index, trading_period_2_open, trading_period_2_close):
            if self.swing.swing_type == "HIGH":
                if leftCandle["High"] < rightCandle["Low"]:
                    if (leftCandle.index >= self.swing.time):
                        if (leftCandle["Close"] > self.swing.price_level) or (middleCandle["Close"] > self.swing.price_level) or (rightCandle["Close"] > self.swing.price_level):
                            green_fvg = FVG(rightCandle.index, rightCandle["Low"], leftCandle["High"], "GREEN")
                            self.FVG_list.append(green_fvg)

            elif self.swing.swing_type == "LOW":
                if leftCandle["Low"] > rightCandle["High"]:
                    if (leftCandle.index >= self.swing.time):
                        if (leftCandle["Close"] < self.swing.price_level) or (middleCandle["Close"] < self.swing.price_level) or (rightCandle["Close"] < self.swing.price_level):
                            red_fvg = FVG(rightCandle.index, rightCandle["High"], leftCandle["Low"], "RED")
                            self.FVG_list.append(red_fvg)

class Swing:
    def __init__(self, time, price_level, swing_type):
        self.time = time
        self.price_level = price_level
        self.swing_type = swing_type # HIGH LOW

        self.FVG_list = FVGList(self)
    
    def isSwingHigh(threeCandles):
        leftCandle = threeCandles.iloc[0]
        middleCandle = threeCandles.iloc[1]
        rightCandle = threeCandles.iloc[2]

        return (leftCandle["High"] <= middleCandle["High"]) and (rightCandle["High"] <= middleCandle["High"])

    def isSwingLow(threeCandles):
        leftCandle = threeCandles.iloc[0]
        middleCandle = threeCandles.iloc[1]
        rightCandle = threeCandles.iloc[2]

        return (leftCandle["Low"] >= middleCandle["Low"]) and (rightCandle["Low"] >= middleCandle["Low"])

    def __str__(self):
        return f"Swing at time {self.time} at price level {self.price_level}"

class SwingList:
    def __init__(self, breach, sl=[]):
        self.swing_list = sl
        self.breach = breach

    def append(self, threeCandles):
        middleCandle = threeCandles.iloc[-2]
        middleCandleTime = middleCandle.index
        swing = -1

        if Swing.isSwingHigh(threeCandles):
            swing = Swing(middleCandleTime, middleCandle["High"], "HIGH")

        if Swing.isSwingLow(threeCandles):
            swing = Swing(middleCandleTime,middleCandle["Low"], "LOW")

        if swing != -1:            
            if (swing.time > self.breach.time):
                if (self.breach.breach_type=="SELLSIDE" and swing.swing_type=="HIGH"):
                    self.swing_list.append(swing)
                elif (self.breach.breach_type=="BUYSIDE" and swing.swing_type=="LOW"):
                    self.swing_list.append(swing)
                else:
                    print("[INFO] Not a valid swing high or low")

class Breach:
    def __init__(self, time, price_level, breach_type):
        self.time = time
        self.price_level = price_level
        self.breach_type = breach_type
        
        self.swings = SwingList(self)
    
    def __str__(self):
        return f"Breach at time {self.time} at price level {self.price_level}"
    
class BreachList:
    def __init__(self, liquidity_line, bl=[]):
        self.breach_list = bl
        self.liquidity_line = liquidity_line
    
    def append(self, potential_breach):
        # append potential candles
        if (self.liquidity_line.liquidty_type == "SELLSIDE") and (potential_breach["Low"] <= self.liquidity_line.price_level):
            breach = Breach(potential_breach.index, potential_breach["Low"])
            self.breach_list.append(breach)

        if (self.liquidity_line.liquidty_type == "BUYSIDE") and (potential_breach["High"] >= self.liquidity_line.price_level):
            breach = Breach(potential_breach.index, potential_breach["High"])
            self.breach_list.append(breach)
            
class LiquidityLine:
    def __init__(self, time, price_level, liquidity_type):
        self.time = time
        self.price_level = price_level
        self.liquidity_type = liquidity_type

        self.breach_list = BreachList(self)
    
    def get_primary_liquidity():
        current_time = tc.get_today()
        dataForLiquidity = yf.download(tickers=security, start=tc.get_delta_trading_date(
            security, current_time.date(), -1), end=current_time.date(), interval='1d')

        dummyDatetime = datetime.combine(tc.get_delta_trading_date(
            security, current_time.date(), -1), time(16, 00, 0))

        pSellsideLiquidity = LiquidityLine(
            dummyDatetime, dataForLiquidity["Low"][0], "SELLSIDE")
        pBuysideLiquidity = LiquidityLine(
            dummyDatetime, dataForLiquidity["High"][0], "BUYSIDE")

        print(pBuysideLiquidity)
        print(pSellsideLiquidity)

        return [pSellsideLiquidity, pBuysideLiquidity]

    def __str__(self):
        return f"{self.liquidity_type} liquidity line at time {self.time} at price level {self.price_level}"


class CandidateTrades():
    def __init__(self):
        self.trade_orders = []
        self.trade_times = []
    
    def append(self, fvg, allSwingHighs, allSwingLows):

        if fvg.FVG_type == "RED" and (fvg.time + timedelta(minutes=tc.INTERVAL)) not in self.trade_times:
            FVGtime = fvg.time + timedelta(minutes=tc.INTERVAL)
            entryPrice = fvg.entry
            stopLimit = fvg.stop_loss

            pSwingThreshold = entryPrice - 10

            takeProfitPrice = float("inf")
                takeProfitTime = -1
                for potential in allSwingLows:
                    if potential < fvg and swing_lows[potential] < pSwingThreshold:
                        if pSwingThreshold-swing_lows[potential] < pSwingThreshold-takeProfitPrice:
                            takeProfitPrice = swing_lows[potential]
                            takeProfitTime = potential

                if takeProfitPrice != float("inf"):
                    positionSize = 250 / ((stopLimit-entryPrice)*10)

                    tradeOrder = TradeOrder(
                        FVGtime, entryPrice, stopLimit, takeProfitPrice, positionSize)
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

                tradeOrder = TradeOrder(
                    FVGtime, entryPrice, stopLimit, takeProfitPrice, positionSize)
                candidateTrades.append(tradeOrder)

    return candidateTrades

class TradeOrder:
    def __init__(self, timeFound, entry, stop_limit, take_profit, position_size):
        self.time_found = timeFound
        self.entry = entry
        self.stop_limit = stop_limit
        self.take_profit = take_profit
        self.position_size = position_size

    def __str__(self):
        return f"TradeOrder: \n \
            Time Found: {self.time_found}, Entry Price: {self.entry:0.2f}\n \
            Stop Limit: {self.stop_limit}, Take Profit: {self.take_profit}\n \
                Position Size: {self.position_size}\n\n"