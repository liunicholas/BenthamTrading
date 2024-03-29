import yfinance as yf
from datetime import datetime, time, timedelta

import trading_clock as tc
from util import *
from data import *

trading_period_1_open = "10:00"
trading_period_1_close = "11:00"
trading_period_2_open = "14:00"
trading_period_2_close = "15:00"

portfolio_size = 50000
max_drawdown = 0.005*portfolio_size

INTERVAL = 5  # minutes

class FVG:
    def __init__(self, time, entry, FVG_type, logger):
        self.time = time
        self.entry = entry
        self.FVG_type = FVG_type #"GREEN" "RED"
        self.logger = logger

    def __str__(self):
        return f"[FVG] {self.FVG_type} at time {self.time} at entry {self.entry}"

class FVGList(list):
    def __init__(self, swing, logger):
        self.swing = swing
        self.logger = logger
    
    def append(self, threeCandles, liquidity_line):
        # FVG is during trading period 10-11, 14-15 
        # After Swing High: Green FVG - 3rd low > 1st high, above swing high pl
        # After Swing Low: Red FVG - 3rd high < 1st low, below swing low pl

        leftCandle = threeCandles[0:1]
        middleCandle = threeCandles[1:2]
        rightCandle = threeCandles[2:3]

        liquidity_line_level = liquidity_line.price_level
        
        if tc.datetime_is_between(middleCandle.index.item(), trading_period_1_open, trading_period_1_close) or tc.datetime_is_between(middleCandle.index.item(), trading_period_2_open, trading_period_2_close):
            if self.swing.swing_type == "HIGH":
                if (leftCandle["High"][-1] < rightCandle["Low"][-1]) and (rightCandle.index.item() >= self.swing.time) and (rightCandle["Low"][-1] > liquidity_line_level):
                    green_fvg = FVG(rightCandle.index.item()+timedelta(minutes=INTERVAL), rightCandle["Low"][-1], "GREEN", self.logger)

                    super().append(green_fvg)
                    self.logger.log(str(green_fvg))

            elif self.swing.swing_type == "LOW":
                if (leftCandle["Low"][-1] > rightCandle["High"][-1]) and (rightCandle.index.item() >= self.swing.time) and (rightCandle["High"][-1] < liquidity_line_level):
                    red_fvg = FVG(rightCandle.index.item()+timedelta(minutes=INTERVAL), rightCandle["High"][-1], "RED", self.logger)
                    
                    super().append(red_fvg)
                    self.logger.log(str(red_fvg))
            
            else:
                print(f"[ERROR] Swing type error for \"{self.swing.swing_type}\"")

class Swing:
    def __init__(self, time, price_level, swing_type, logger=None):
        self.time = time
        self.price_level = price_level
        self.swing_type = swing_type # HIGH LOW
        self.logger = logger

        if logger is not None:
            self.FVG_list = FVGList(self, logger)
    
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
    def __init__(self, breach, logger, *args):
        super().__init__(*args)
        self.breach = breach
        self.logger = logger

    def append(self, threeCandles):
        middleCandle = threeCandles[-2:-1]
        middleCandleTime = middleCandle.index.item()
        swing = None

        if Swing.isSwingHigh(threeCandles):
            swing = Swing(middleCandleTime,
                          middleCandle["High"][-1], "HIGH", self.logger)

        if Swing.isSwingLow(threeCandles):
            swing = Swing(middleCandleTime,
                          middleCandle["Low"][-1], "LOW", self.logger)

        if swing is not None:            
            if (swing.time > self.breach.time):
                if (self.breach.breach_type=="SELLSIDE" and swing.swing_type=="HIGH" and swing.price_level>self.breach.liquidity_line.price_level):
                    super().append(swing)
                    self.logger.log(str(swing))
                elif (self.breach.breach_type == "BUYSIDE" and swing.swing_type=="LOW" and swing.price_level < self.breach.liquidity_line.price_level):
                    super().append(swing)
                    self.logger.log(str(swing))
                else:
                    self.logger.log(f"[INFO] Not a valid swing high or low at {swing.time}")

class Breach:
    def __init__(self, time, liquidity_line, price_level, breach_type, logger):
        self.time = time
        self.price_level = price_level
        self.breach_type = breach_type
        self.liquidity_line = liquidity_line
        self.logger = logger

        self.swing_list = SwingList(self, logger)
    
    def __str__(self):
        return f"[BREACH] {self.breach_type} at time {self.time} at price level {self.price_level}"
    
class BreachList(list):
    def __init__(self, liquidity_line, logger, *args):
        super().__init__(*args)
        self.liquidity_line = liquidity_line
        self.logger = logger

    def append(self, potential_breach):
        if (self.liquidity_line.liquidity_type == "SELLSIDE") and (potential_breach["Low"][-1] <= self.liquidity_line.price_level):
            breach = Breach(potential_breach.index.item(), self.liquidity_line, potential_breach["Low"][-1], "SELLSIDE", self.logger)
            super().append(breach)
            self.logger.log(str(breach))

        if (self.liquidity_line.liquidity_type == "BUYSIDE") and (potential_breach["High"][-1] >= self.liquidity_line.price_level):
            breach = Breach(potential_breach.index.item(), self.liquidity_line, potential_breach["High"][-1], "BUYSIDE", self.logger)
            super().append(breach)
            self.logger.log(str(breach))
            
class LiquidityLine:
    def __init__(self, time, price_level, liquidity_type, logger):
        self.time = time
        self.price_level = price_level
        self.liquidity_type = liquidity_type
        self.logger = logger

        self.breach_list = BreachList(self, logger)

    def __str__(self):
        return f"{self.liquidity_type} liquidity line at time {self.time} at price level {self.price_level}"

class LiquidityLineList(list):
    def __init__(self, security_type, security_data, logger, *args):
        super().__init__(*args)
        self.security_type = security_type
        self.logger = logger

        self.current_queue_period = "AM_session"
        self.queued_buyside_liquidity_line = None
        self.queued_sellside_liquidity_line = None

        self.get_primary_liquidity(security_data)
 
    def append(self, todays_data):
        # no point in looking for new liquidity lines here
        if len(todays_data) < 3:
            return
        
        if tc.datetime_is_between(tc.get_today(), "9:30", "12:05"):
            current_time_period = "AM_session"
        elif tc.datetime_is_between(tc.get_today(), "12:10", "13:35"):
            current_time_period = "lunch_session"
        elif tc.datetime_is_between(tc.get_today(), "13:40", "16:00"):
            current_time_period = "PM_session"
        else:
            # no need to queue new liquidity lines
            return
        
        if self.current_queue_period == "AM_session" and current_time_period == "lunch_session":
            if self.queued_buyside_liquidity_line is not None:
                super().append(self.queued_buyside_liquidity_line)
                self.logger.log("[INFO] Adding AM " + str(self.queued_buyside_liquidity_line))
            
            if self.queued_sellside_liquidity_line is not None:
                super().append(self.queued_sellside_liquidity_line)
                self.logger.log("[INFO] Adding AM " + str(self.queued_sellside_liquidity_line))

            self.queued_buyside_liquidity_line = None
            self.queued_sellside_liquidity_line = None

            self.current_queue_period = "lunch_session"
        elif self.current_queue_period == "lunch_session" and current_time_period == "PM_session":
            if self.queued_buyside_liquidity_line is not None:
                super().append(self.queued_buyside_liquidity_line)
                self.logger.log("[INFO] Adding Lunch " +
                                str(self.queued_buyside_liquidity_line))

            if self.queued_sellside_liquidity_line is not None:
                super().append(self.queued_sellside_liquidity_line)
                self.logger.log("[INFO] Adding Lunch " +
                                str(self.queued_sellside_liquidity_line))

            self.queued_buyside_liquidity_line = None
            self.queued_sellside_liquidity_line = None

            self.current_queue_period = "PM_session"
        else:
            pass
        
        # not looking for more liquidity lines
        if self.current_queue_period == "PM_session":
            return
        
        new_high_level = todays_data[-2:-1]["High"][-1]
        new_low_level = todays_data[-2:-1]["Low"][-1]
        new_line_time = todays_data[-2:-1].index.item()
        if Swing.isSwingHigh(todays_data[-3:]):
            if self.queued_buyside_liquidity_line is None or new_high_level > self.queued_buyside_liquidity_line.price_level:
                self.queued_buyside_liquidity_line = LiquidityLine(
                    new_line_time, new_high_level, "BUYSIDE", self.logger)
        elif Swing.isSwingLow(todays_data[-3:]):
            if self.queued_sellside_liquidity_line is None or new_low_level < self.queued_sellside_liquidity_line.price_level:
                self.queued_sellside_liquidity_line = LiquidityLine(
                    new_line_time, new_low_level, "SELLSIDE", self.logger)
        else:
            pass

        return

    def prune_liquidity_lines(self, candidate_trades):
        liquidity_levels_used = []
        for trade in candidate_trades.trade_orders:
            liquidity_levels_used.append(trade.stop_limit)
        
        # no need to prune any lines
        if not liquidity_levels_used:
            return

        pruned_liquidity_lines = []
        for liquidity_line in self:
            if min(map(lambda used_level: abs(liquidity_line.price_level-used_level), liquidity_levels_used)) < 1:
                self.logger.log(f"[INFO] {liquidity_line.liquidity_type} Liquidity Line from {liquidity_line.time} at {liquidity_line.price_level} removed.")
            else:
                pruned_liquidity_lines.append(liquidity_line)
                 
        self = pruned_liquidity_lines
    
    def get_primary_liquidity(self, security_data):
        current_time = tc.get_today()
        last_trading_day = tc.get_delta_trading_date(self.security_type, current_time.date(), -1)

        # choose previous session data based on whether it was a half day or not
        dataForLiquidity = security_data["yesterdata"]
        if last_trading_day not in tc.half_day_before and last_trading_day not in tc.half_day_after:
            previous_session_data = dataForLiquidity.between_time("13:30", "16:00")
        else:
            previous_session_data = dataForLiquidity.between_time("9:30", "13:00")

        def get_session_swings(session_data):
            takeProfitSwingLows, takeProfitSwingHighs = [], []

            for i in session_data.index[:-2]:
                threeCandles = session_data[i:i+timedelta(minutes=INTERVAL*2)]
                middleCandle = threeCandles[-2:-1]
                middleCandleTime = middleCandle.index.item()

                if Swing.isSwingHigh(threeCandles):
                    swing = Swing(middleCandleTime,
                                  middleCandle["High"][-1], "HIGH")
                    takeProfitSwingHighs.append(swing)

                if Swing.isSwingLow(threeCandles):
                    swing = Swing(middleCandleTime,
                                  middleCandle["Low"][-1], "LOW")
                    takeProfitSwingLows.append(swing)

            return takeProfitSwingLows, takeProfitSwingHighs
        
        takeProfitSwingLows, takeProfitSwingHighs = get_session_swings(previous_session_data)

        # get buyside liquidity line
        takeProfitSwingHighs.sort(key=lambda swing: swing.price_level, reverse=True)
        highest_swing_high = takeProfitSwingHighs[0]

        high_time, previous_high = previous_session_data.High.idxmax(), previous_session_data.loc[previous_session_data.High.idxmax(), "High"]

        buyside_level = highest_swing_high.price_level if highest_swing_high.time >= high_time else previous_high
        buyside_time = highest_swing_high.time if highest_swing_high.time >= high_time else high_time

        pBuysideLiquidity = LiquidityLine(buyside_time, buyside_level, "BUYSIDE", self.logger)
        self.logger.log("[INFO] Previous day " + str(pBuysideLiquidity))
        super().append(pBuysideLiquidity)

        # get sellside liquidity line
        takeProfitSwingLows.sort(key=lambda swing: swing.price_level)
        lowest_swing_low = takeProfitSwingLows[0]

        low_time, previous_low = previous_session_data.Low.idxmin(), previous_session_data.loc[previous_session_data.Low.idxmin(), "Low"]

        sellside_level = lowest_swing_low.price_level if lowest_swing_low.time >= low_time else previous_low
        sellside_time = lowest_swing_low.time if lowest_swing_low.time >= low_time else low_time

        pSellsideLiquidity = LiquidityLine(sellside_time, sellside_level, "SELLSIDE", self.logger)
        self.logger.log("[INFO] Previous day " + str(pSellsideLiquidity))
        super().append(pSellsideLiquidity)

class CandidateTrades():
    def __init__(self, logger):
        self.trade_orders = []
        self.trade_times = []
        self.logger = logger
    
    def append(self, silver_bullet_object, fvg):
        FVG_time = fvg.time
        entry_price = fvg.entry

        security = silver_bullet_object.security
        take_profit_margin = silver_bullet_object.take_profit_margin
        stop_loss_margin = silver_bullet_object.stop_loss_margin
        leverage_multiplier = silver_bullet_object.leverage_multiplier

        liquidity_lines = silver_bullet_object.liquidity_lines
        trade_type = None

        if fvg.FVG_type == "RED" and FVG_time not in self.trade_times:
            # find take profit price and stop limit price
            profit_threshold = entry_price - take_profit_margin
            stop_limit_threshold = entry_price + stop_loss_margin

            potential_take_profit_lines = []
            potential_stop_limit_lines = []
            for liquidity_line in liquidity_lines:
                if liquidity_line.time < FVG_time and liquidity_line.price_level < profit_threshold:
                    potential_take_profit_lines.append(liquidity_line)
                if liquidity_line.time < FVG_time and liquidity_line.price_level > stop_limit_threshold:
                    potential_stop_limit_lines.append(liquidity_line)

            potential_take_profit_lines.sort(key=lambda line: line.time, reverse=True)
            potential_stop_limit_lines.sort(key=lambda line: line.time, reverse=True)

            try:
                take_profit_price = potential_take_profit_lines[0].price_level
                stop_limit_price = potential_stop_limit_lines[0].price_level
            except:
                self.logger.log(f"[INFO] No Valid Take Proft/Stop Limit For FVG at {FVG_time}")
            else:
                trade_type = "SHORT"

        if fvg.FVG_type == "GREEN" and FVG_time not in self.trade_times:
            # find take profit price and stop limit price
            profit_threshold = entry_price + take_profit_margin
            stop_limit_threshold = entry_price - stop_loss_margin

            potential_take_profit_lines = []
            potential_stop_limit_lines = []
            for liquidity_line in liquidity_lines:
                if liquidity_line.time < FVG_time and liquidity_line.price_level > profit_threshold:
                    potential_take_profit_lines.append(liquidity_line)
                if liquidity_line.time < FVG_time and liquidity_line.price_level < stop_limit_threshold:
                    potential_stop_limit_lines.append(liquidity_line)

            potential_take_profit_lines.sort(key=lambda line: line.time, reverse=True)
            potential_stop_limit_lines.sort(key=lambda line: line.time, reverse=True)

            try:
                take_profit_price = potential_take_profit_lines[0].price_level
                stop_limit_price = potential_stop_limit_lines[0].price_level
            except:
                self.logger.log(f"[INFO] No Valid Take Proft/Stop Limit For FVG at {FVG_time}")
            else:
                trade_type = "LONG"

        if trade_type:    
            position_size = max_drawdown / (abs(entry_price-stop_limit_price)*leverage_multiplier)
            trade_order = TradeOrder(security, FVG_time, entry_price, stop_limit_price, take_profit_price, position_size, trade_type, leverage_multiplier)
            self.trade_orders.append(trade_order)
            self.trade_times.append(FVG_time)
            fvg.logger.log(str(trade_order))
            fvg.logger.sum_log(str(trade_order))

class SilverBullet():
    def __init__(self, security, security_type, take_profit_margin, stop_loss_margin, leverage_multiplier, VERBOSE=False, OVERRIDE=False):
        self.logger = StrategyLogger(security=security, strategy_name="SilverBullet", date=tc.get_today().date())
        self.VERBOSE = VERBOSE

        self.security = security
        self.security_type = security_type
        self.take_profit_margin = take_profit_margin
        self.stop_loss_margin = stop_loss_margin
        self.leverage_multiplier = leverage_multiplier

        self.security_data = SecurityData(security, security_type)
        self.security_data.get_day_data("yesterdata", tc.get_today(), interval=INTERVAL, delta=-1)

        self.liquidity_lines = LiquidityLineList(security_type, self.security_data, self.logger)
        
        self.candidate_trades = CandidateTrades(self.logger)
        self.last_cycled_data_point, self.last_pulled_minute = None, None

        # catch up system
        if not OVERRIDE and tc.real_time()-timedelta(minutes=INTERVAL) > tc.localize(datetime.combine(tc.get_today().date(), tc.NYSE_open)):
            start_time = tc.localize(datetime.combine(tc.get_today().date(), tc.NYSE_open))
            if tc.real_time() > tc.localize(datetime.combine(tc.get_today().date(), tc.NYSE_close)):
                end_time = tc.localize(datetime.combine(tc.get_today().date(), tc.NYSE_close))
            else:
                end_time = tc.real_time()
            
            self.simulate_cycles(start_time, end_time)
    
    def simulate_cycles(self, start_time, end_time):
        for simulated_time in tc.get_generator([start_time, end_time]):
            tc.override(simulated_time)
            self.run_cycle(tc.get_today())

        tc.turn_off_override()
    
    def run_cycle(self, current_time):
        print(f"[INFO] Cycle run at {current_time} for {self.security}")

        # helper function for cycling a liquidity line on new data
        def cycle_liquidity_line(liquidity_line, todays_data):
            liquidity_line.breach_list.append(todays_data[-1:])
            # iterate through breaches in each liquidity line if swings can form
            if len(todays_data) >= 3:
                for breach in liquidity_line.breach_list:
                    breach.swing_list.append(todays_data[-3:])

                    # iterate through swings in each breach
                    for swing in breach.swing_list:
                        swing.FVG_list.append(todays_data[-3:], liquidity_line)

                        # iterate through FVGs in each swing
                        for FVG in swing.FVG_list:
                            self.candidate_trades.append(self, FVG)

        # only get data if the minute time is on an interval mark or data has never been pulled before
        if self.last_pulled_minute is None or (current_time.minute % INTERVAL == 0 and current_time.minute != self.last_pulled_minute):
            print(f"[INFO] Retrieving data for {self.security} at {current_time}")
            self.security_data.get_day_data("todaysData", current_time, interval=INTERVAL, delta=0)
            self.last_pulled_minute = current_time.minute

        todays_data = self.security_data["todaysData"]
        if self.VERBOSE: print(todays_data.tail())

        # only iterate through procedure if data exist and it is new data
        if (not todays_data.empty) and ((self.last_cycled_data_point is None) or (self.last_cycled_data_point < todays_data.index[-1])):
            print(f"[INFO] New data found at {current_time}, running silver bullet cycle for {self.security}")

            # remove liquidity lines that have been assigned a trade
            self.liquidity_lines.prune_liquidity_lines(self.candidate_trades)
            # incrementally add liquidity lines throughout the day depending on trading period
            self.liquidity_lines.append(todays_data)
            
            # cycle silver bullet on established liquidity lines
            for liquidity_line in self.liquidity_lines:
                cycle_liquidity_line(liquidity_line, todays_data)
            
            # cycle silver bullet on queued liquidity lines that will be added later
            queued_liquidity_lines = [
                self.liquidity_lines.queued_buyside_liquidity_line,
                self.liquidity_lines.queued_sellside_liquidity_line
            ]
            
            for liquidity_line in queued_liquidity_lines:
                if liquidity_line is not None:
                    cycle_liquidity_line(liquidity_line, todays_data)

            self.last_cycled_data_point = todays_data.index[-1]