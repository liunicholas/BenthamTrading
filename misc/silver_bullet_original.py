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

SWING_INTERVAL = 5
INTERVAL = 5  # minutes

class FVG:
    def __init__(self, time, entry, stop_loss, FVG_type, logger):
        self.time = time
        self.entry = entry
        self.stop_loss = stop_loss
        self.FVG_type = FVG_type #"GREEN" "RED"
        self.logger = logger

    def __str__(self):
        return f"[FVG] {self.FVG_type} at time {self.time} at entry {self.entry} and stop loss {self.stop_loss}"

class FVGList(list):
    def __init__(self, swing, logger):
        self.swing = swing
        self.logger = logger
    
    def append(self, threeCandles, liquidity_line):
        # FVG is during trading period 10-11, 14-15 DONE
        # After Swing High: Green FVG - 3rd low > 1st high, above swing high pl
        # After Swing Low: Red FVG - 3rd high < 1st low, below swing low pl
        # note that 5 minute delay is added to fvg time when creating the trade order

        leftCandle = threeCandles[0:1]
        middleCandle = threeCandles[1:2]
        rightCandle = threeCandles[2:3]

        liquidity_line_level = liquidity_line.price_level
        
        if tc.datetime_is_between(middleCandle.index.item(), trading_period_1_open, trading_period_1_close) or tc.datetime_is_between(middleCandle.index.item(), trading_period_2_open, trading_period_2_close):
            if self.swing.swing_type == "HIGH":
                if leftCandle["High"][-1] < rightCandle["Low"][-1]:
                    if (leftCandle.index.item() >= self.swing.time):
                        if rightCandle["Low"][-1] > liquidity_line_level:
                            if (leftCandle["Close"][-1] > self.swing.price_level) or (middleCandle["Close"][-1] > self.swing.price_level) or (rightCandle["Close"][-1] > self.swing.price_level):
                                
                                # experimenting with changing the stop loss value

                                # green_fvg = FVG(rightCandle.index.item(), rightCandle["Low"][-1], leftCandle["High"][-1], "GREEN")
                                green_fvg = FVG(rightCandle.index.item(
                                ), rightCandle["Low"][-1], liquidity_line_level-0.25, "GREEN", self.logger)

                                super().append(green_fvg)
                                self.logger.log(str(green_fvg))

            elif self.swing.swing_type == "LOW":
                if leftCandle["Low"][-1] > rightCandle["High"][-1]:
                    if (leftCandle.index.item() >= self.swing.time):
                        if rightCandle["High"][-1] < liquidity_line_level:
                            if (leftCandle["Close"][-1] < self.swing.price_level) or (middleCandle["Close"][-1] < self.swing.price_level) or (rightCandle["Close"][-1] < self.swing.price_level):
                                
                                # experimenting with changing the stop loss value

                                # red_fvg = FVG(rightCandle.index.item(
                                # ), rightCandle["High"][-1], leftCandle["Low"][-1], "RED")

                                red_fvg = FVG(rightCandle.index.item(
                                ), rightCandle["High"][-1], liquidity_line_level+0.25, "RED", self.logger)
                                super().append(red_fvg)
                                self.logger.log(str(red_fvg))
            
            else:
                print(f"[ERROR] Swing type error for \"{self.swing.swing_type}\"")

class Swing:
    def __init__(self, time, price_level, swing_type, logger):
        self.time = time
        self.price_level = price_level
        self.swing_type = swing_type # HIGH LOW
        self.logger = logger

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
        swing = -1

        if Swing.isSwingHigh(threeCandles):
            swing = Swing(middleCandleTime,
                          middleCandle["High"][-1], "HIGH", self.logger)

        if Swing.isSwingLow(threeCandles):
            swing = Swing(middleCandleTime,
                          middleCandle["Low"][-1], "LOW", self.logger)

        if swing != -1:            
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
            breach = Breach(potential_breach.index.item(
            ), self.liquidity_line, potential_breach["Low"][-1], "SELLSIDE", self.logger)
            super().append(breach)
            self.logger.log(str(breach))

        if (self.liquidity_line.liquidity_type == "BUYSIDE") and (potential_breach["High"][-1] >= self.liquidity_line.price_level):
            breach = Breach(potential_breach.index.item(
            ), self.liquidity_line, potential_breach["High"][-1], "BUYSIDE", self.logger)
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
        self.GOT_SECONDARY_LIQUIDITY = False

        self.get_primary_liquidity(tc.get_today(), security_data)
        print(self)
    
    # def append(self, current_time, security_data):
    #     update_liquidity_line_times = {
    #         "AM_session": ("10:00", "11:00"),
    #         "lunch_session": ("12:00", "13:30"),
    #         # "PM_session": ("14:00", "15:00"),
    #     }
    #     pass

    def prune_liquidity_lines(self, todays_data):
        pruned_liquidity_lines = []
        for liquidity_line in self:
            if liquidity_line.liquidity_type == "BUYSIDE" and todays_data[-1:]["High"][-1]/liquidity_line.price_level > 1.01:
                self.logger.log(f"[INFO] Removed liquidity line: {liquidity_line}")
            elif liquidity_line.liquidity_type == "SELLSIDE" and todays_data[-1:]["Low"][-1]/liquidity_line.price_level < 0.99:
                self.logger.log(f"[INFO] Removed liquidity line: {liquidity_line}")
            else:
                pruned_liquidity_lines.append(liquidity_line)
        
        self = pruned_liquidity_lines
    
    def get_primary_liquidity(self, current_time, security_data):
        security_type = self.security_type
        last_trading_day = tc.get_delta_trading_date(
            security_type, current_time.date(), -1)

        dataForLiquidity = security_data["yesterdata"]
        if last_trading_day not in tc.half_day_before:
            previous_session_data = dataForLiquidity.between_time("13:30", "16:00")
        else:
            previous_session_data = dataForLiquidity.between_time("9:30", "13:30")

        previous_high = previous_session_data["High"].max()
        previous_low = previous_session_data["Low"].min()

        dummyDatetime = datetime.combine(tc.get_delta_trading_date(
            security_type, current_time.date(), -1), time(16, 00, 0))

        pSellsideLiquidity = LiquidityLine(
            dummyDatetime, previous_low, "SELLSIDE", self.logger)
        pBuysideLiquidity = LiquidityLine(
            dummyDatetime, previous_high, "BUYSIDE", self.logger)

        self.logger.log("[INFO] Previous day high " + str(pBuysideLiquidity))
        self.logger.log("[INFO] Previous day low " + str(pSellsideLiquidity))

        super().append(pSellsideLiquidity)
        super().append(pBuysideLiquidity)   

    def get_secondary_liquidity(self, current_time, security_data):
        if not self.GOT_SECONDARY_LIQUIDITY:
            print(
                f"[INFO] ADDING LIQUIDITY LINES FROM AM SESSION FOR {{self.security}}")
            todaysData = security_data["todaysData"].between_time(
                "10:00", "11:00")

            amHigh = LiquidityLine(
                current_time, todaysData.max()["High"], "BUYSIDE", self.logger)
            amLow = LiquidityLine(
                current_time, todaysData.min()["Low"], "SELLSIDE", self.logger)

            self.logger.log("[INFO] AM High " + str(amHigh))
            self.logger.log("[INFO] AM Low " + str(amLow))

            super().append(amHigh)
            super().append(amLow)

            self.GOT_SECONDARY_LIQUIDITY = True     

class CandidateTrades():
    def __init__(self):
        self.trade_orders = []
        self.trade_times = []
    
    def append(self, security, take_profit_margin, stop_loss_margin, leverage_multiplier, fvg, all_swing_lows, all_swing_highs):
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
            fvg.logger.log(str(trade_order))
            fvg.logger.sum_log(str(trade_order))

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
            fvg.logger.log(str(trade_order))
            fvg.logger.sum_log(str(trade_order))

class SilverBullet():
    def __init__(self, security, security_type, take_profit_margin, stop_loss_margin, leverage_multiplier, OVERRIDE=False):
        self.logger = StrategyLogger(security=security, strategy_name="SilverBullet", date=tc.get_today().date())

        self.security = security
        self.security_type = security_type
        self.take_profit_margin = take_profit_margin
        self.stop_loss_margin = stop_loss_margin
        self.leverage_multiplier = leverage_multiplier

        self.security_data = SecurityData(security, security_type)
        self.security_data.get_day_data("yesterdata", tc.get_today(),
                                interval=INTERVAL, delta=-1)
        self.takeProfitSwingLows, self.takeProfitSwingHighs = self.get_previous_day_swings()

        self.liquidity_lines = LiquidityLineList(security_type, self.security_data, self.logger)

        self.candidate_trades = CandidateTrades()
        self.last_known_data_point = None
        self.last_pulled_minute = -1

        if not OVERRIDE and tc.real_time()-timedelta(minutes=INTERVAL) > tc.localize(datetime.combine(tc.get_today().date(), tc.NYSE_open)):
            start_time = tc.localize(datetime.combine(
                tc.get_today().date(), tc.NYSE_open))
            if tc.real_time() > tc.localize(datetime.combine(tc.get_today().date(), tc.NYSE_close)):
                end_time = tc.localize(datetime.combine(
                    tc.get_today().date(), tc.NYSE_close))
            else:
                end_time = tc.real_time()
            
            self.simulate_cycles(start_time, end_time)
    
    def simulate_cycles(self, start_time, end_time):
        this_generator = tc.get_generator([start_time, end_time])

        for simulated_time in this_generator:
            tc.override(simulated_time)
            current_time = tc.get_today()

            self.run_cycle(current_time)

        tc.turn_off_override()
    
    def run_cycle(self, current_time):
        print(f"[INFO] Cycle run at {current_time} for {self.security}")

        # only get data if the minute time is on an interval mark or data has never been pulled before
        if self.last_pulled_minute == -1 or (current_time.minute % INTERVAL == 0 and current_time.minute != self.last_pulled_minute):
            print(f"[INFO] Retrieving data for {self.security} at {current_time}")
            self.security_data.get_day_data("todaysData", current_time, interval=INTERVAL, delta=0)
            self.last_pulled_minute = current_time.minute

        # add new liquidity lines after AM session
        if tc.datetime_is_between(current_time, "11:00", "11:01"):
            self.liquidity_lines.get_secondary_liquidity(current_time, self.security_data)

        todays_data = self.security_data["todaysData"]
        # print(todays_data.tail())
        # print(todays_data)

        # only iterate through procedure on new data
        if (not todays_data.empty) and ((self.last_known_data_point is None) or (self.last_known_data_point < todays_data.index[-1])):
            print(f"[INFO] New data found at {current_time}, running silver bullet cycle for {self.security}")
            # self.liquidity_lines.prune_liquidity_lines(todays_data)
            
            for liquidity_line in self.liquidity_lines:
                liquidity_line.breach_list.append(todays_data[-1:])
                # iterate through breaches in each liquidity line if swings can form
                if len(todays_data) >= 3:
                    middleCandleTime = todays_data.index[-2]

                    for breach in liquidity_line.breach_list:
                        breach.swing_list.append(todays_data[-3:])

                        # iterate through swings in each breach
                        for swing in breach.swing_list:
                            swing.FVG_list.append(
                                todays_data[-3:], liquidity_line)

                            # iterate through FVGs in each swing
                            for FVG in swing.FVG_list:
                                self.candidate_trades.append(
                                    self.security, self.take_profit_margin, self.stop_loss_margin, self.leverage_multiplier, 
                                    FVG, self.takeProfitSwingLows, self.takeProfitSwingHighs)

            self.last_known_data_point = todays_data.index[-1]

            # separate function for take profit points
            if len(todays_data) >= 3:
                middleCandleTime = todays_data.index[-2]
                if Swing.isSwingHigh(todays_data[-3:]):
                    swingHigh = Swing(
                        middleCandleTime, todays_data.iloc[-2]["High"], "HIGH", self.logger)
                    self.takeProfitSwingHighs.append(swingHigh)

                if Swing.isSwingLow(todays_data[-3:]):
                    swingLow = Swing(
                        middleCandleTime, todays_data.iloc[-2]["Low"], "LOW", self.logger)
                    self.takeProfitSwingLows.append(swingLow)
            
    def get_previous_day_swings(self):
        yesterdata = self.security_data["yesterdata"]
        takeProfitSwingLows, takeProfitSwingHighs = [], []

        for i in yesterdata.index[:-2]:
            threeCandles = yesterdata[i:i+timedelta(minutes=SWING_INTERVAL*2)]
            middleCandle = threeCandles[-2:-1]
            middleCandleTime = middleCandle.index.item()

            if Swing.isSwingHigh(threeCandles):
                swing = Swing(middleCandleTime,
                              middleCandle["High"][-1], "HIGH", self.logger)
                takeProfitSwingHighs.append(swing)

            if Swing.isSwingLow(threeCandles):
                swing = Swing(middleCandleTime,
                              middleCandle["Low"][-1], "LOW", self.logger)
                takeProfitSwingLows.append(swing)

        return takeProfitSwingLows, takeProfitSwingHighs

    
        
