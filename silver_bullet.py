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

max_drawdown = 0.05*50000
leverage_multiplier = 10

def log(line):
    with open(f"logs/candidate_trades_{tc.get_today().date()}.txt", "a") as f:
        f.write(line + "\n")

class FVG:
    def __init__(self, time, entry, stop_loss, FVG_type):
        self.time = time
        self.entry = entry
        self.stop_loss = stop_loss
        self.FVG_type = FVG_type #"GREEN" "RED"

    def __str__(self):
        return f"[FVG] {self.FVG_type} at time {self.time} at entry {self.entry} and stop loss {self.stop_loss}"

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
                            print(green_fvg)
                            log(str(green_fvg))

            elif self.swing.swing_type == "LOW":
                if leftCandle["Low"] > rightCandle["High"]:
                    if (leftCandle.index >= self.swing.time):
                        if (leftCandle["Close"] < self.swing.price_level) or (middleCandle["Close"] < self.swing.price_level) or (rightCandle["Close"] < self.swing.price_level):
                            red_fvg = FVG(rightCandle.index, rightCandle["High"], leftCandle["Low"], "RED")
                            self.FVG_list.append(red_fvg)
                            print(red_fvg)
                            log(str(red_fvg))


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
        return f"[SWING] {self.swing_type} at time {self.time} at price level {self.price_level}"

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
                    print(swing)
                    log(str(swing))
                elif (self.breach.breach_type=="BUYSIDE" and swing.swing_type=="LOW"):
                    self.swing_list.append(swing)
                    print(swing)
                    log(str(swing))
                else:
                    print("[INFO] Not a valid swing high or low")

class Breach:
    def __init__(self, time, price_level, breach_type):
        self.time = time
        self.price_level = price_level
        self.breach_type = breach_type
        
        self.swings = SwingList(self)
    
    def __str__(self):
        return f"[BREACH] {self.breach_type} at time {self.time} at price level {self.price_level}"
    
class BreachList:
    def __init__(self, liquidity_line, bl=[]):
        self.breach_list = bl
        self.liquidity_line = liquidity_line
    
    def append(self, potential_take_profit_breach):
        # append potential_take_profit candles
        if (self.liquidity_line.liquidty_type == "SELLSIDE") and (potential_take_profit_breach["Low"] <= self.liquidity_line.price_level):
            breach = Breach(potential_take_profit_breach.index, potential_take_profit_breach["Low"])
            self.breach_list.append(breach)
            print(breach)
            log(str(breach))

        if (self.liquidity_line.liquidty_type == "BUYSIDE") and (potential_take_profit_breach["High"] >= self.liquidity_line.price_level):
            breach = Breach(potential_take_profit_breach.index, potential_take_profit_breach["High"])
            self.breach_list.append(breach)
            print(breach)
            log(str(breach))
            
class LiquidityLine:
    def __init__(self, time, price_level, liquidity_type):
        self.time = time
        self.price_level = price_level
        self.liquidity_type = liquidity_type

        self.breach_list = BreachList(self)

    def __str__(self):
        return f"{self.liquidity_type} liquidity line at time {self.time} at price level {self.price_level}"

class TradeOrder:
    def __init__(self, timeFound, entry, stop_limit, take_profit, position_size):
        self.time_found = timeFound
        self.entry = entry
        self.stop_limit = stop_limit
        self.take_profit = take_profit
        self.position_size = position_size

    def __str__(self):
        return f"[TRADE ORDER]: \n \
            Time Found: {self.time_found}, Entry Price: {self.entry:0.2f}\n \
            Stop Limit: {self.stop_limit}, Take Profit: {self.take_profit}\n \
                Position Size: {self.position_size}\n\n"
    
class CandidateTrades():
    def __init__(self):
        self.trade_orders = []
        self.trade_times = []
    
    def append(self, fvg, all_swing_lows, all_swing_highs):
        if fvg.FVG_type == "RED" and (fvg.time + timedelta(minutes=tc.INTERVAL)) not in self.trade_times:
            FVG_time = fvg.time + timedelta(minutes=tc.INTERVAL)
            entry_price = fvg.entry
            stop_limit = fvg.stop_loss

            p_swing_threshold = entry_price - 10

            take_profit_price = float("inf")
            for potential_take_profit in all_swing_lows:
                if potential_take_profit < FVG_time and all_swing_lows[potential_take_profit] < p_swing_threshold:
                    if p_swing_threshold-all_swing_lows[potential_take_profit] < p_swing_threshold-take_profit_price:
                        take_profit_price = all_swing_lows[potential_take_profit]

            if take_profit_price != float("inf"):
                position_size = max_drawdown / ((stop_limit-entry_price)*leverage_multiplier)     
                trade_order = TradeOrder(
                    FVG_time, entry_price, stop_limit, take_profit_price, position_size)
                self.trade_orders.append(trade_order)
                print(trade_order)
                log(str(trade_order))

                
        if fvg.FVG_type == "GREEN" and (fvg.time + timedelta(minutes=tc.INTERVAL)) not in self.trade_times:
            FVG_time = fvg.time + timedelta(minutes=tc.INTERVAL)
            entry_price = fvg.entry
            stop_limit = fvg.stop_loss

            p_swing_threshold = entry_price + 10

            take_profit_price = float("inf")
            for potential_take_profit in all_swing_highs:
                if potential_take_profit < FVG_time and all_swing_highs[potential_take_profit] > p_swing_threshold:
                    if all_swing_highs[potential_take_profit]-p_swing_threshold < take_profit_price-p_swing_threshold:
                        take_profit_price = all_swing_highs[potential_take_profit]

            if take_profit_price != float("inf"):
                position_size = max_drawdown / ((entry_price-stop_limit)*leverage_multiplier)
                trade_order = TradeOrder(FVG_time, entry_price, stop_limit, take_profit_price, position_size)
                self.trade_orders.append(trade_order)
                print(trade_order)
                log(str(trade_order))

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
    log(str(pBuysideLiquidity))
    log(str(pSellsideLiquidity))

    return [pSellsideLiquidity, pBuysideLiquidity]