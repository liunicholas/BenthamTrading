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
leverage_multiplier = 10

SWING_INTERVAL = 5
INTERVAL = 5  # minutes

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
    
    def append(self, threeCandles, logger):
        # FVG is during trading period 10-11, 14-15 DONE
        # After Swing High: Green FVG - 3rd low > 1st high, above swing high pl
        # After Swing Low: Red FVG - 3rd high < 1st low, below swing low pl
        # note that 5 minute delay is added to fvg time when creating the trade order

        leftCandle = threeCandles[0:1]
        middleCandle = threeCandles[1:2]
        rightCandle = threeCandles[2:3]
        
        if tc.datetime_is_between(middleCandle.index.item(), trading_period_1_open, trading_period_1_close) or tc.datetime_is_between(middleCandle.index.item(), trading_period_2_open, trading_period_2_close):
            if self.swing.swing_type == "HIGH":
                if leftCandle["High"][-1] < rightCandle["Low"][-1]:
                    if (leftCandle.index.item() >= self.swing.time):
                        if (leftCandle["Close"][-1] > self.swing.price_level) or (middleCandle["Close"][-1] > self.swing.price_level) or (rightCandle["Close"][-1] > self.swing.price_level):
                            green_fvg = FVG(rightCandle.index.item(
                            ), rightCandle["Low"][-1], leftCandle["High"][-1], "GREEN")
                            super().append(green_fvg)
                            logger.log(str(green_fvg))

            elif self.swing.swing_type == "LOW":
                if leftCandle["Low"][-1] > rightCandle["High"][-1]:
                    if (leftCandle.index.item() >= self.swing.time):
                        if (leftCandle["Close"][-1] < self.swing.price_level) or (middleCandle["Close"][-1] < self.swing.price_level) or (rightCandle["Close"][-1] < self.swing.price_level):
                            red_fvg = FVG(rightCandle.index.item(
                            ), rightCandle["High"][-1], leftCandle["Low"][-1], "RED")
                            super().append(red_fvg)
                            logger.log(str(red_fvg))

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

    def append(self, threeCandles, logger):
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
                    logger.log(str(swing))
                elif (self.breach.breach_type == "BUYSIDE" and swing.swing_type=="LOW" and swing.price_level < self.breach.liquidity_line.price_level):
                    super().append(swing)
                    logger.log(str(swing))
                else:
                    logger.log(f"[INFO] Not a valid swing high or low at {swing.time}")

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

    def append(self, potential_breach, logger):
        if (self.liquidity_line.liquidity_type == "SELLSIDE") and (potential_breach["Low"][-1] <= self.liquidity_line.price_level):
            breach = Breach(potential_breach.index.item(), self.liquidity_line, potential_breach["Low"][-1], "SELLSIDE")
            super().append(breach)
            logger.log(str(breach))

        if (self.liquidity_line.liquidity_type == "BUYSIDE") and (potential_breach["High"][-1] >= self.liquidity_line.price_level):
            breach = Breach(potential_breach.index.item(),self.liquidity_line,potential_breach["High"][-1], "BUYSIDE")
            super().append(breach)
            logger.log(str(breach))
            
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
    
    def append(self, security, take_profit_margin, stop_loss_margin, fvg, all_swing_lows, all_swing_highs, logger):
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
            logger.log(str(trade_order))
            logger.sum_log(str(trade_order))


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
            logger.log(str(trade_order))
            logger.sum_log(str(trade_order))

class SilverBullet():
    def __init__(self, security, security_type, take_profit_margin, stop_loss_margin, OVERRIDE=False):
        self.logger = StrategyLogger(security=security, strategy_name="SilverBullet", date=tc.get_today().date())

        self.security = security
        self.security_type = security_type
        self.take_profit_margin = take_profit_margin
        self.stop_loss_margin = stop_loss_margin

        self.security_data = SecurityData(security, security_type)
        self.security_data.get_day_data("yesterdata", tc.get_today(),
                                interval=INTERVAL, delta=-1)
        self.takeProfitSwingLows, self.takeProfitSwingHighs = self.get_previous_day_swings()

        self.liquidity_lines = self.get_primary_liquidity(current_time=tc.get_today())
        self.GOT_SECONDARY_LIQUIDITY = False

        self.candidate_trades = CandidateTrades()
        self.last_known_data_point = None
        self.last_pulled_minute = -1

        if not OVERRIDE and tc.real_time()-timedelta(minutes=INTERVAL) > tc.localize(datetime.combine(tc.get_today().date(), tc.exchange_openclose[security_type][0])):
            start_time = tc.localize(datetime.combine(
                tc.get_today().date(), tc.exchange_openclose[security_type][0]))
            if tc.real_time() > tc.localize(datetime.combine(tc.get_today().date(), tc.exchange_openclose[security_type][1])):
                end_time = tc.localize(datetime.combine(
                    tc.get_today().date(), tc.exchange_openclose[security_type][1]))
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
        if tc.datetime_is_between(current_time, "11:00", "11:05") and not self.GOT_SECONDARY_LIQUIDITY:
            print(f"[INFO] ADDING LIQUIDITY LINES FROM AM SESSION FOR {{self.security}}")
            self.liquidity_lines += self.get_secondary_liquidity(current_time)
            self.GOT_SECONDARY_LIQUIDITY = True

        todays_data = self.security_data["todaysData"]
        # print(todays_data.tail())

        # only iterate through procedure on new data
        if (not todays_data.empty) and ((self.last_known_data_point is None) or (self.last_known_data_point < todays_data.index[-1])):
            print(f"[INFO] New data found at {current_time}, running silver bullet cycle for {self.security}")
            pruned_liquidity_lines = []
            
            for liquidity_line in self.liquidity_lines:
                if liquidity_line.liquidity_type == "BUYSIDE" and todays_data[-1:]["High"][-1]/liquidity_line.price_level > 1.02:
                    self.logger.log(f"[INFO] Removed liquidity line: {liquidity_line}")
                elif liquidity_line.liquidity_type == "SELLSIDE" and todays_data[-1:]["Low"][-1]/liquidity_line.price_level < 0.98:
                    self.logger.log(f"[INFO] Removed liquidity line: {liquidity_line}")
                else:
                    pruned_liquidity_lines.append(liquidity_line)

                    liquidity_line.breach_list.append(todays_data[-1:], self.logger)
                    # iterate through breaches in each liquidity line if swings can form
                    if len(todays_data) >= 3:
                        middleCandleTime = todays_data.index[-2]

                        for breach in liquidity_line.breach_list:
                            breach.swing_list.append(todays_data[-3:], self.logger)

                            # iterate through swings in each breach
                            for swing in breach.swing_list:
                                swing.FVG_list.append(todays_data[-3:], self.logger)

                                # iterate through FVGs in each swing
                                for FVG in swing.FVG_list:
                                    self.candidate_trades.append(
                                        self.security, self.take_profit_margin, self.stop_loss_margin, FVG, self.takeProfitSwingLows, self.takeProfitSwingHighs, self.logger)

            self.last_known_data_point = todays_data.index[-1]
            self.liquidity_lines = pruned_liquidity_lines

            # separate function for take profit points
            if len(todays_data) >= 3:
                middleCandleTime = todays_data.index[-2]
                if Swing.isSwingHigh(todays_data[-3:]):
                    swingHigh = Swing(
                        middleCandleTime, todays_data.iloc[-2]["High"], "HIGH")
                    self.takeProfitSwingHighs.append(swingHigh)

                if Swing.isSwingLow(todays_data[-3:]):
                    swingLow = Swing(
                        middleCandleTime, todays_data.iloc[-2]["Low"], "LOW")
                    self.takeProfitSwingLows.append(swingLow)
            
    def get_previous_day_swings(self):
        yesterdata = self.security_data["yesterdata"]
        takeProfitSwingLows, takeProfitSwingHighs = [], []

        for i in yesterdata.index[:-2]:
            threeCandles = yesterdata[i:i+timedelta(minutes=SWING_INTERVAL*2)]
            middleCandle = threeCandles[-2:-1]
            middleCandleTime = middleCandle.index.item()

            if Swing.isSwingHigh(threeCandles):
                swing = Swing(middleCandleTime, middleCandle["High"][-1], "HIGH")
                takeProfitSwingHighs.append(swing)

            if Swing.isSwingLow(threeCandles):
                swing = Swing(middleCandleTime, middleCandle["Low"][-1], "LOW")
                takeProfitSwingLows.append(swing)

        return takeProfitSwingLows, takeProfitSwingHighs


    def get_primary_liquidity(self, current_time):
        security_type = self.security_type

        # dummyDatetime = datetime.combine(tc.get_delta_trading_date(
        #     security_type, current_time.date(), -1), time(16, 00, 0))

        # pSellsideLiquidity = LiquidityLine(
        #     dummyDatetime, dataForLiquidity["Low"][0], "SELLSIDE")
        # pBuysideLiquidity = LiquidityLine(
        #     dummyDatetime, dataForLiquidity["High"][0], "BUYSIDE")

        # self.logger.log("[INFO] Previous day high " + str(pBuysideLiquidity))
        # self.logger.log("[INFO] Previous day low " + str(pSellsideLiquidity))

        dataForLiquidity = self.security_data["yesterdata"]
        if current_time.date() - timedelta(days=1) not in tc.federal_holidays:
            pm_session_data = dataForLiquidity.between_time("13:30", "16:00")

            pm_high = pm_session_data["High"].max()
            pm_low = pm_session_data["Low"].min()

            dummyDatetime = datetime.combine(tc.get_delta_trading_date(
                security_type, current_time.date(), -1), time(16, 00, 0))

            pSellsideLiquidity = LiquidityLine(dummyDatetime, pm_low, "SELLSIDE")
            pBuysideLiquidity = LiquidityLine(dummyDatetime, pm_high, "BUYSIDE")

            self.logger.log("[INFO] Previous day PM high " + str(pBuysideLiquidity))
            self.logger.log("[INFO] Previous day PM low " + str(pSellsideLiquidity))
        else:
            am_session_data = dataForLiquidity.between_time("9:30", "13:30")

            am_high = am_session_data["High"].max()
            am_low = am_session_data["Low"].min()

            dummyDatetime = datetime.combine(tc.get_delta_trading_date(
                security_type, current_time.date(), -1), time(16, 00, 0))

            pSellsideLiquidity = LiquidityLine(
                dummyDatetime, am_low, "SELLSIDE")
            pBuysideLiquidity = LiquidityLine(
                dummyDatetime, am_high, "BUYSIDE")

            self.logger.log("[INFO] Previous day AM high " +
                            str(pBuysideLiquidity))
            self.logger.log("[INFO] Previous day AM low " +
                            str(pSellsideLiquidity))

        return [pSellsideLiquidity, pBuysideLiquidity]


    def get_secondary_liquidity(self, current_time):
        security = self.security
        todaysData = self.security_data["todaysData"]

        amHigh = LiquidityLine(
            current_time, todaysData.max()["High"], "BUYSIDE")
        amLow = LiquidityLine(
            current_time, todaysData.min()["Low"], "SELLSIDE")

        # openPrice = todaysData[0:1]["Open"].item()
        # closePrice = todaysData[-1:]["Close"].item()

        # if openPrice >= closePrice:
        #     amOpen = LiquidityLine(
        #         current_time, openPrice, "BUYSIDE")
        #     amClose = LiquidityLine(
        #         current_time, closePrice, "SELLSIDE")
        # else:
        #     amOpen = LiquidityLine(
        #         current_time, openPrice, "SELLSIDE")
        #     amClose = LiquidityLine(
        #         current_time, closePrice, "BUYSIDE")

        # self.logger.log("[INFO] AM Open " + str(amOpen))
        self.logger.log("[INFO] AM High " + str(amHigh))
        self.logger.log("[INFO] AM Low " + str(amLow))
        # self.logger.log("[INFO] AM Close " + str(amClose))

        # return [amHigh, amLow, amOpen, amClose]
        return [amHigh, amLow]
        
