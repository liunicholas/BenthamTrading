from trader import *
import trading_clock as tc
from datetime import datetime, date, time, timedelta
import yfinance as yf
import pytz
import time

datetime_range = [tc.localize(datetime(2023, 6, 19, 9, 30, 0)),
                  tc.localize(datetime(2023, 6, 19, 16, 0, 0))]

# currentTime = datetime_range[0]
# waitTime = 0

start = datetime_range[0]
end = datetime_range[1]
this_generator = tc.get_generator([start, end])

tc.override(datetime_range[0])
with open(f"trade_logs/candidate_trades_{tc.get_today().date()}.txt", "w") as f:
    f.write("Proprietary Information of Bentham Trading \n")

spx_data = SecurityData(security=security)
spx_data.get_day_data("yesterdata", tc.get_today(), interval=INTERVAL, delta=-1)

takeProfitSwingLows, takeProfitSwingHighs = get_previous_day_swings(spx_data["yesterdata"])

liquidity_lines = get_primary_liquidity(tc.get_today())
candidate_trades = CandidateTrades()
last_known_data_point = None

for simulated_time in this_generator:
    tc.override(simulated_time)

    current_time = tc.get_today()

    if (current_time.minute % INTERVAL) == 0:
        spx_data.get_day_data("todaysData", current_time,
                              interval=INTERVAL, delta=0)
        
    last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs = run_cycle(spx_data, current_time, last_known_data_point, liquidity_lines,
                                                                                                                    candidate_trades, takeProfitSwingLows, takeProfitSwingHighs)

