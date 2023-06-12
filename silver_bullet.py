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
    def line_exists_in_file(file_path, target_line):
        with open(file_path, 'r') as file:
            for line in file:
                if line.strip() == target_line:
                    return True
        return False

    with open(f"logs/candidate_trades_{tc.get_today().date()}.txt", "a") as f:
        if not line_exists_in_file(f"logs/candidate_trades_{tc.get_today().date()}.txt", line):
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
    
    def append(self, threeCandles):
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
                            log(str(green_fvg))

            elif self.swing.swing_type == "LOW":
                if leftCandle["Low"][-1] > rightCandle["High"][-1]:
                    if (leftCandle.index.item() >= self.swing.time):
                        if (leftCandle["Close"][-1] < self.swing.price_level) or (middleCandle["Close"][-1] < self.swing.price_level) or (rightCandle["Close"][-1] < self.swing.price_level):
                            red_fvg = FVG(rightCandle.index.item(
                            ), rightCandle["High"][-1], leftCandle["Low"][-1], "RED")
                            super().append(red_fvg)
                            print(red_fvg)
                            log(str(red_fvg))

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

    def append(self, threeCandles):
        middleCandle = threeCandles[-2:-1]
        middleCandleTime = middleCandle.index.item()
        swing = -1

        if Swing.isSwingHigh(threeCandles):
            swing = Swing(middleCandleTime, middleCandle["High"][-1], "HIGH")

        if Swing.isSwingLow(threeCandles):
            swing = Swing(middleCandleTime, middleCandle["Low"][-1], "LOW")

        if swing != -1:            
            if (swing.time > self.breach.time):
                if (self.breach.breach_type=="SELLSIDE" and swing.swing_type=="HIGH"):
                    super().append(swing)
                    print(swing)
                    log(str(swing))
                elif (self.breach.breach_type=="BUYSIDE" and swing.swing_type=="LOW"):
                    super().append(swing)
                    print(swing)
                    log(str(swing))
                else:
                    print("[INFO] Not a valid swing high or low")
                    log(f"[INFO {swing.time}] Not a valid swing high or low")

class Breach:
    def __init__(self, time, price_level, breach_type):
        self.time = time
        self.price_level = price_level
        self.breach_type = breach_type
        
        self.swing_list = SwingList(self)
    
    def __str__(self):
        return f"[BREACH] {self.breach_type} at time {self.time} at price level {self.price_level}"
    
class BreachList(list):
    def __init__(self, liquidity_line, *args):
        super().__init__(*args)
        self.liquidity_line = liquidity_line

    def append(self, potential_breach):
        if (self.liquidity_line.liquidity_type == "SELLSIDE") and (potential_breach["Low"][-1] <= self.liquidity_line.price_level):
            breach = Breach(potential_breach.index.item(),potential_breach["Low"][-1], "SELLSIDE")
            super().append(breach)
            print(breach)
            log(str(breach))

        if (self.liquidity_line.liquidity_type == "BUYSIDE") and (potential_breach["High"][-1] >= self.liquidity_line.price_level):
            breach = Breach(potential_breach.index.item(),potential_breach["High"][-1], "BUYSIDE")
            super().append(breach)
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
        FVG_time = fvg.time + timedelta(minutes=tc.INTERVAL)
        if fvg.FVG_type == "RED" and FVG_time not in self.trade_times:
            entry_price = fvg.entry
            stop_limit = fvg.stop_loss

            p_swing_threshold = entry_price - 10

            take_profit_price = float("inf")
            for potential_take_profit in all_swing_lows:
                if potential_take_profit.time < FVG_time and potential_take_profit.price_level < p_swing_threshold:
                    if abs(p_swing_threshold-potential_take_profit.price_level) < abs(p_swing_threshold-take_profit_price):
                        take_profit_price = potential_take_profit.price_level
            
            if take_profit_price != float("inf"):
                position_size = max_drawdown / ((stop_limit-entry_price)*leverage_multiplier)     
                trade_order = TradeOrder(
                    FVG_time, entry_price, stop_limit, take_profit_price, position_size)
                self.trade_orders.append(trade_order)
                self.trade_times.append(FVG_time)
                print(trade_order)
                log(str(trade_order))


        if fvg.FVG_type == "GREEN" and FVG_time not in self.trade_times:
            entry_price = fvg.entry
            stop_limit = fvg.stop_loss

            p_swing_threshold = entry_price + 10

            take_profit_price = float("inf")
            for potential_take_profit in all_swing_highs:
                if potential_take_profit.time < FVG_time and potential_take_profit.price_level > p_swing_threshold:
                    if abs(potential_take_profit.price_level-p_swing_threshold) < abs(take_profit_price-p_swing_threshold):
                        take_profit_price = potential_take_profit.price_level

            if take_profit_price != float("inf"):
                position_size = max_drawdown / ((entry_price-stop_limit)*leverage_multiplier)
                trade_order = TradeOrder(FVG_time, entry_price, stop_limit, take_profit_price, position_size)
                self.trade_orders.append(trade_order)
                self.trade_times.append(FVG_time)
                print(trade_order)
                log(str(trade_order))

def get_primary_liquidity():
    current_time = tc.get_today()
    dataForLiquidity = yf.download(progress=False, tickers=security, start=tc.get_delta_trading_date(
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