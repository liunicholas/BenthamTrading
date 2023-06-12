from trader import *
import trading_clock as tc
from datetime import datetime, date, time, timedelta
import yfinance as yf
import pytz
import time

datetime_range = [tc.localize(datetime(2023, 6, 8, 9, 30, 0)),
                  tc.localize(datetime(2023, 6, 8, 16, 0, 0))]

# currentTime = datetime_range[0]
# waitTime = 0

start = datetime_range[0]
end = datetime_range[1]
this_generator = tc.get_generator([start, end])

tc.override(datetime_range[0])
takeProfitSwingLows, takeProfitSwingHighs = get_previous_day_swings(tc.get_today())
# log(' '.join([str(swing) for swing in takeProfitSwingHighs]))

liquidity_lines = get_primary_liquidity()
candidate_trades = CandidateTrades()
last_known_data_point = None

for simulated_time in this_generator:
    tc.override(simulated_time)
    if not os.path.exists(f"logs/candidate_trades_{tc.get_today().date()}.txt"):
        with open(f"logs/candidate_trades_{tc.get_today().date()}.txt", "w") as f:
            f.write("Proprietary Information of Bentham Trading ")

    current_time = tc.get_today()
    last_known_data_point, liquidity_lines, candidate_trades, takeProfitSwingLows, takeProfitSwingHighs = run_cycle(current_time, last_known_data_point, liquidity_lines,
                                                                                                                    candidate_trades, takeProfitSwingLows, takeProfitSwingHighs)