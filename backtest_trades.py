from trader import *
import trading_clock as tc
from datetime import datetime, date, time, timedelta
import yfinance as yf
import pytz
import time

datetime_range = [tc.localize(datetime(2023, 6, 21, 9, 30, 0)),
                  tc.localize(datetime(2023, 6, 21, 16, 0, 0))]

# currentTime = datetime_range[0]
# waitTime = 0

security = "^spx"
start = datetime_range[0]
end = datetime_range[1]
this_generator = tc.get_generator([start, end])

tc.override(datetime_range[0])
with open(f"trade_logs/{security}_candidate_trades_{tc.get_today().date()}.txt", "w") as f:
    f.write("Proprietary Information of Bentham Trading \n")

security_data = SecurityData(security=security)
security_data.get_day_data("yesterdata", tc.get_today(), interval=INTERVAL, delta=-1)

takeProfitSwingLows, takeProfitSwingHighs = get_previous_day_swings(security_data["yesterdata"])

liquidity_lines = get_primary_liquidity(security, tc.get_today())
candidate_trades = CandidateTrades()
last_known_data_point = None

for simulated_time in this_generator:
    tc.override(simulated_time)

    current_time = tc.get_today()

    if (current_time.minute % INTERVAL) == 0:
        security_data.get_day_data("todaysData", current_time,
                              interval=INTERVAL, delta=0)
        
    last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs = run_cycle(security, security_data, current_time, last_known_data_point, liquidity_lines,
                                                                                                                    candidate_trades, takeProfitSwingLows, takeProfitSwingHighs)

