from __future__ import print_function
import trading_clock as tc
import yfinance as yf
from datetime import datetime, date, time, timedelta
from util import *

trading_period_1_open = "10:00"
trading_period_1_close = "11:00"
trading_period_2_open = "14:00"
trading_period_2_close = "15:00"

portfolio_size = 50000
max_drawdown = 0.005*portfolio_size
leverage_multiplier = 10
margin = 5000
# max_position_size = 

SWING_INTERVAL = 5
INTERVAL = 5  # minutes

def log(security, line):
    # print(tc.get_today())
    def line_exists_in_file(file_path, target_line):
        with open(file_path, 'r') as file:
            for line in file:
                if line.strip() == target_line:
                    return True
        return False

    with open(f"trade_logs/{security}_candidate_trades_{tc.get_today().date()}.txt", "a") as f:
        if not line_exists_in_file(f"trade_logs/{security}_candidate_trades_{tc.get_today().date()}.txt", line):
            f.write(line + "\n")

class FVG:
    def __init__(self, time, entry, stop_loss, FVG_type):
        self.time = time
        self.entry = entry
        self.stop_loss = stop_loss
        self.FVG_type = FVG_type #"GREEN" "RED"

    def __str__(self):
        return f"[FVG] {self.FVG_type} at time {self.time} at entry {self.entry} and stop loss {self.stop_loss}"

class FVGList(list):
    def __init__(self, swing):
        self.swing = swing
    
    def append(self, security, threeCandles):
        # FVG is during trading period 10-11, 14-15 DONE
        # After Swing High: Green FVG - 3rd low > 1st high, above swing high pl
        # After Swing Low: Red FVG - 3rd high < 1st low, below swing low pl

        leftCandle = threeCandles[0:1]
        middleCandle = threeCandles[1:2]
        rightCandle = threeCandles[2:3]
        
        if tc.datetime_is_between(leftCandle.index.item(), trading_period_1_open, trading_period_1_close) or tc.datetime_is_between(leftCandle.index.item(), trading_period_2_open, trading_period_2_close):
            if self.swing.swing_type == "HIGH":
                if leftCandle["High"][-1] < rightCandle["Low"][-1]:
                    if (leftCandle.index.item() >= self.swing.time):
                        if (leftCandle["Close"][-1] > self.swing.price_level) or (middleCandle["Close"][-1] > self.swing.price_level) or (rightCandle["Close"][-1] > self.swing.price_level):
                            green_fvg = FVG(rightCandle.index.item(
                            ), rightCandle["Low"][-1], leftCandle["High"][-1], "GREEN")
                            super().append(green_fvg)
                            print(green_fvg)
                            log(security, str(green_fvg))

            elif self.swing.swing_type == "LOW":
                if leftCandle["Low"][-1] > rightCandle["High"][-1]:
                    if (leftCandle.index.item() >= self.swing.time):
                        if (leftCandle["Close"][-1] < self.swing.price_level) or (middleCandle["Close"][-1] < self.swing.price_level) or (rightCandle["Close"][-1] < self.swing.price_level):
                            red_fvg = FVG(rightCandle.index.item(
                            ), rightCandle["High"][-1], leftCandle["Low"][-1], "RED")
                            super().append(red_fvg)
                            print(red_fvg)
                            log(security, str(red_fvg))

class Swing:
    def __init__(self, time, price_level, swing_type):
        self.time = time
        self.price_level = price_level
        self.swing_type = swing_type # HIGH LOW

        self.FVG_list = FVGList(self)
    
    def isSwingHigh(threeCandles):
        leftCandle = threeCandles[0:1]
        middleCandle = threeCandles[1:2]
        rightCandle = threeCandles[2:3]

        return (leftCandle["High"][-1] <= middleCandle["High"][-1]) and (rightCandle["High"][-1] <= middleCandle["High"][-1])

    def isSwingLow(threeCandles):
        leftCandle = threeCandles[0:1]
        middleCandle = threeCandles[1:2]
        rightCandle = threeCandles[2:3]

        return (leftCandle["Low"][-1] >= middleCandle["Low"][-1]) and (rightCandle["Low"][-1] >= middleCandle["Low"][-1])

    def __str__(self):
        return f"[SWING] {self.swing_type} at time {self.time} at price level {self.price_level}"

class SwingList(list):
    def __init__(self, breach, *args):
        super().__init__(*args)
        self.breach = breach

    def append(self, security, threeCandles):
        middleCandle = threeCandles[-2:-1]
        middleCandleTime = middleCandle.index.item()
        swing = -1

        if Swing.isSwingHigh(threeCandles):
            swing = Swing(middleCandleTime, middleCandle["High"][-1], "HIGH")

        if Swing.isSwingLow(threeCandles):
            swing = Swing(middleCandleTime, middleCandle["Low"][-1], "LOW")

        if swing != -1:            
            if (swing.time > self.breach.time):
                if (self.breach.breach_type=="SELLSIDE" and swing.swing_type=="HIGH" and swing.price_level>self.breach.liquidity_line.price_level):
                    super().append(swing)
                    print(swing)
                    log(security, str(swing))
                elif (self.breach.breach_type == "BUYSIDE" and swing.swing_type=="LOW" and swing.price_level < self.breach.liquidity_line.price_level):
                    super().append(swing)
                    print(swing)
                    log(security, str(swing))
                else:
                    print("[INFO] Not a valid swing high or low")

class Breach:
    def __init__(self, time, liquidity_line, price_level, breach_type):
        self.time = time
        self.price_level = price_level
        self.breach_type = breach_type
        self.liquidity_line = liquidity_line

        self.swing_list = SwingList(self)
    
    def __str__(self):
        return f"[BREACH] {self.breach_type} at time {self.time} at price level {self.price_level}"
    
class BreachList(list):
    def __init__(self, liquidity_line, *args):
        super().__init__(*args)
        self.liquidity_line = liquidity_line

    def append(self, security, potential_breach):
        if (self.liquidity_line.liquidity_type == "SELLSIDE") and (potential_breach["Low"][-1] <= self.liquidity_line.price_level):
            breach = Breach(potential_breach.index.item(), self.liquidity_line, potential_breach["Low"][-1], "SELLSIDE")
            super().append(breach)
            print(breach)
            log(security, str(breach))

        if (self.liquidity_line.liquidity_type == "BUYSIDE") and (potential_breach["High"][-1] >= self.liquidity_line.price_level):
            breach = Breach(potential_breach.index.item(),self.liquidity_line,potential_breach["High"][-1], "BUYSIDE")
            super().append(breach)
            print(breach)
            log(security, str(breach))
            
class LiquidityLine:
    def __init__(self, time, price_level, liquidity_type):
        self.time = time
        self.price_level = price_level
        self.liquidity_type = liquidity_type

        self.breach_list = BreachList(self)

    def __str__(self):
        return f"{self.liquidity_type} liquidity line at time {self.time} at price level {self.price_level}"
    
class CandidateTrades():
    def __init__(self):
        self.trade_orders = []
        self.trade_times = []
    
    def append(self, security, take_profit_margin, stop_loss_margin, fvg, all_swing_lows, all_swing_highs):
        FVG_time = fvg.time + timedelta(minutes=INTERVAL)
        entry_price = fvg.entry
        stop_limit_price = fvg.stop_loss

        if fvg.FVG_type == "RED" and FVG_time not in self.trade_times:
            # find take profit price
            profit_swing_threshold = entry_price - take_profit_margin
            take_profit_price = float("inf")

            for potential_take_profit in all_swing_lows:
                if potential_take_profit.time < FVG_time and potential_take_profit.price_level < profit_swing_threshold:
                    if abs(profit_swing_threshold-potential_take_profit.price_level) < abs(profit_swing_threshold-take_profit_price):
                        take_profit_price = potential_take_profit.price_level
            
            if take_profit_price == float("inf"):
                take_profit_price = profit_swing_threshold

            # find stop limit price
            loss_swing_threshold = entry_price + stop_loss_margin

            if not stop_limit_price > loss_swing_threshold:
                stop_limit_price = float("inf")

                for potential_stop_limit in all_swing_highs:
                    if potential_stop_limit.time < FVG_time and potential_stop_limit.price_level > loss_swing_threshold:
                        if abs(loss_swing_threshold-potential_stop_limit.price_level) < abs(loss_swing_threshold-stop_limit_price):
                            stop_limit_price = potential_stop_limit.price_level
                
                if stop_limit_price == float("inf"):
                    stop_limit_price = loss_swing_threshold

            position_size = max_drawdown / ((stop_limit_price-entry_price)*leverage_multiplier)
            trade_order = TradeOrder(
                security, FVG_time, entry_price, stop_limit_price, take_profit_price, position_size, "SHORT", leverage_multiplier)
            self.trade_orders.append(trade_order)
            self.trade_times.append(FVG_time)
            print(trade_order)
            log(security, str(trade_order))


        if fvg.FVG_type == "GREEN" and FVG_time not in self.trade_times:
            # find take profit price
            profit_swing_threshold = entry_price + take_profit_margin
            take_profit_price = float("inf")

            for potential_take_profit in all_swing_highs:
                if potential_take_profit.time < FVG_time and potential_take_profit.price_level > profit_swing_threshold:
                    if abs(potential_take_profit.price_level-profit_swing_threshold) < abs(take_profit_price-profit_swing_threshold):
                        take_profit_price = potential_take_profit.price_level

            if take_profit_price == float("inf"):
                take_profit_price = profit_swing_threshold
            
            # find stop limit price
            loss_swing_threshold = entry_price - stop_loss_margin
            if not stop_limit_price < loss_swing_threshold:
                stop_limit_price = float("inf")

                for potential_stop_limit in all_swing_lows:
                    if potential_stop_limit.time < FVG_time and potential_stop_limit.price_level < loss_swing_threshold:
                        if abs(loss_swing_threshold-potential_stop_limit.price_level) < abs(loss_swing_threshold-stop_limit_price):
                            stop_limit_price = potential_stop_limit.price_level
                
                if stop_limit_price == float("inf"):
                    stop_limit_price = loss_swing_threshold
                
            position_size = max_drawdown / ((entry_price-stop_limit_price)*leverage_multiplier)
            trade_order = TradeOrder(security, FVG_time, entry_price, stop_limit_price, take_profit_price, position_size, "LONG", leverage_multiplier)
            self.trade_orders.append(trade_order)
            self.trade_times.append(FVG_time)
            print(trade_order)
            log(security, str(trade_order))

def get_previous_day_swings(yesterdata):
    # print(yesterdata)
    # print("CT", current_time)
    # print(yesterdata)
    takeProfitSwingLows, takeProfitSwingHighs = [], []

    for i in yesterdata.index[:-2]:
        threeCandles = yesterdata[i:i+timedelta(minutes=SWING_INTERVAL*2)]
        # print(threeCandles)
        middleCandle = threeCandles[-2:-1]
        middleCandleTime = middleCandle.index.item()

        if Swing.isSwingHigh(threeCandles):
            swing = Swing(middleCandleTime, middleCandle["High"][-1], "HIGH")
            takeProfitSwingHighs.append(swing)

        if Swing.isSwingLow(threeCandles):
            swing = Swing(middleCandleTime, middleCandle["Low"][-1], "LOW")
            takeProfitSwingLows.append(swing)

    return takeProfitSwingLows, takeProfitSwingHighs

def get_primary_liquidity(security, current_time):
    # current_time = tc.get_today()
    dataForLiquidity = yf.download(progress=False, tickers=security, start=tc.get_delta_trading_date(
        security, current_time.date(), -1), end=current_time.date(), interval='1d')
    # print(current_time)
    # print(dataForLiquidity)

    dummyDatetime = datetime.combine(tc.get_delta_trading_date(
        security, current_time.date(), -1), time(16, 00, 0))

    pSellsideLiquidity = LiquidityLine(
        dummyDatetime, dataForLiquidity["Low"][0], "SELLSIDE")
    pBuysideLiquidity = LiquidityLine(
        dummyDatetime, dataForLiquidity["High"][0], "BUYSIDE")

    print(pBuysideLiquidity)
    print(pSellsideLiquidity)
    log(security, str(pBuysideLiquidity))
    log(security, str(pSellsideLiquidity))

    return [pSellsideLiquidity, pBuysideLiquidity]

def get_secondary_liquidity(security, current_time, todaysData):
    amHigh = LiquidityLine(
        current_time, todaysData.max()["High"], "BUYSIDE")
    amLow = LiquidityLine(
        current_time, todaysData.min()["Low"], "SELLSIDE")
    
    openPrice = todaysData[0:1]["Open"]
    closePrice = todaysData[-1:]["Close"]

    if openPrice.item() >= closePrice.item():
        amOpen = LiquidityLine(
            current_time, openPrice.item(), "BUYSIDE")
        amClose = LiquidityLine(
            current_time, closePrice.item(), "SELLSIDE")
    else:
        amOpen = LiquidityLine(
            current_time, openPrice.item(), "SELLSIDE")
        amClose = LiquidityLine(
            current_time, closePrice.item(), "BUYSIDE")


    print("amOpen", amOpen)
    print("amClose", amClose)
    print("amHigh", amHigh)
    print("amLow", amLow)
    log(security, str(amHigh))
    log(security, str(amLow))
    log(security, str(amClose))
    log(security, str(amOpen))

    return [amHigh, amLow, amOpen, amClose]
