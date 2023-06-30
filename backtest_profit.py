from trader import *
import trading_clock as tc
from silver_bullet import *
from util import *
from datetime import datetime

def backtestTradesForSecurity(security):
    this_generator = tc.get_generator([test_date_start, test_date_end])

    security_type = "ETF"
    strategy_name = "SilverBullet"
    trade_log = f"trade_logs/{strategy_name}/{security}/{test_date_start.date()}_{strategy_name}_{security}_candidate_trades.txt"

    trade_orders = []
    with open(trade_log, "r") as f:
        for line in f:
            if "TRADE ORDER" in line:
                temp = []
                for i in range(8):
                    l = f.readline().strip()
                    lsplit = l.split(": ")
                    temp.append(lsplit[-1][:-1])
                print(temp)
                trade_orders.append(TradeOrder(
                    time_found=datetime.strptime(
                        temp[2], "%Y-%m-%d %H:%M:%S%z"),
                    security=temp[1],
                    entry=float(temp[3]),
                    stop_limit=float(temp[4]),
                    take_profit=float(temp[5]),
                    position_size=float(temp[6]),
                    trade_type=temp[0],
                    leverage=int(temp[7])))

    security_data = SecurityData(security, security_type)
    executed_trades = []  # ExecutedTrade objects
    finished_trades = []
    pnl = 0
    for simulated_time in this_generator:
        tc.override(simulated_time)
        current_time = tc.get_today()

        if (current_time.minute % INTERVAL) == 0:
            security_data.get_day_data("todaysData", current_time,
                                       interval=INTERVAL, delta=0)
            # print(security_data["todaysData"])
            price_low = security_data["todaysData"][-1:]["Low"][0]
            price_high = security_data["todaysData"][-1:]["High"][0]
            price_close = security_data["todaysData"][-1:]["Close"][0]
            for to in trade_orders:
                if to.time_found <= current_time:
                    # print("to.time_found <= current_time")
                    if not to.position_opened:
                        # print("here")
                        if to.trade_type == "LONG" and (tc.datetime_is_between(current_time, "10:00", "11:05") or tc.datetime_is_between(current_time, "14:00", "15:05")):
                            if to.entry >= price_low:
                                to.entry_time = current_time
                                to.position_opened = True
                                print(f"{to.trade_type} POSITION OPENED")
                        if to.trade_type == "SHORT" and (tc.datetime_is_between(current_time, "10:00", "11:05") or tc.datetime_is_between(current_time, "14:00", "15:05")):
                            if to.entry <= price_high:
                                to.entry_time = current_time
                                to.position_opened = True
                                print(f"{to.trade_type} POSITION OPENED")

                    if to.position_opened and not to.position_closed:
                        # check if stoploss or take profit or exit by time 3 or 11
                        if tc.datetime_is_between(to.time_found, "9:30", "11:05"):
                            if tc.datetime_is_between(current_time, "10:00", "11:25"):
                                if to.trade_type == "LONG" and to.take_profit <= price_high:
                                    executed_trades.append(ExecutedTrade(
                                        to, to.take_profit, current_time, "TAKE PROFIT"))
                                    to.position_closed = True
                                elif to.trade_type == "LONG" and to.stop_limit >= price_low:
                                    executed_trades.append(ExecutedTrade(
                                        to, to.stop_limit, current_time, "STOMPED"))
                                    to.position_closed = True
                                elif to.trade_type == "SHORT" and to.take_profit >= price_low:
                                    executed_trades.append(ExecutedTrade(
                                        to, to.take_profit, current_time, "TAKE PROFIT"))
                                    to.position_closed = True
                                elif to.trade_type == "SHORT" and to.stop_limit <= price_high:
                                    executed_trades.append(ExecutedTrade(
                                        to, to.stop_limit, current_time, "STOMPED"))
                                    to.position_closed = True
                            elif tc.datetime_is_between(current_time, "11:30", "4:05"):
                                executed_trades.append(ExecutedTrade(
                                    to, price_close, current_time, "TRADE PERIOD END (LIQUIDATE)"))
                                to.position_closed = True

                        elif tc.datetime_is_between(to.time_found, "14:00", "16:05"):
                            if tc.datetime_is_between(current_time, "14:00", "15:30"):
                                if to.trade_type == "LONG" and to.take_profit <= price_high:
                                    executed_trades.append(ExecutedTrade(
                                        to, to.take_profit, current_time, "TAKE PROFIT"))
                                    to.position_closed = True
                                elif to.trade_type == "LONG" and to.stop_limit >= price_low:
                                    executed_trades.append(ExecutedTrade(
                                        to, to.stop_limit, current_time, "STOMPED"))
                                    to.position_closed = True
                                elif to.trade_type == "SHORT" and to.take_profit >= price_low:
                                    executed_trades.append(ExecutedTrade(
                                        to, to.take_profit, current_time, "TAKE PROFIT"))
                                    to.position_closed = True
                                elif to.trade_type == "SHORT" and to.stop_limit <= price_high:
                                    executed_trades.append(ExecutedTrade(
                                        to, to.stop_limit, current_time, "STOMPED"))
                                    to.position_closed = True
                            elif tc.datetime_is_between(current_time, "15:35", "16:05"):
                                executed_trades.append(ExecutedTrade(
                                    to, price_close, current_time, "TRADE PERIOD END (LIQUIDATE)"))
                                to.position_closed = True

    backtest_log = f"backtest_logs/{strategy_name}/{security}/{tc.get_today().date()}_{strategy_name}_{security}_candidate_trades.txt"
    with open(backtest_log, "w") as f:
        total_pnl = 0
        for et in executed_trades:
            f.write(str(et) + "\n")
            print(str(et))
            total_pnl += et.pnl

        print(f"Final PNL ${total_pnl:0.2f}")
        f.write(f"Final PNL ${total_pnl:0.2f} \n")

month = 6
day = 29
test_date_start = tc.localize(datetime(2023, month, day, 9, 35, 0))
test_date_end = tc.localize(datetime(2023, month, day, 16, 0, 0))
for i in range(2):
    backtestTradesForSecurity("^spx")
    backtestTradesForSecurity("^ixic")

    test_date_start = tc.localize(datetime.combine(
        tc.get_last_trading_date("ETF", test_date_start), time(9, 35, 0)))

    test_date_end = tc.localize(datetime.combine(
        tc.get_last_trading_date("ETF", test_date_end), time(16, 00, 0)))
