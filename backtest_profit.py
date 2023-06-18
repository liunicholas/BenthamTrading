from trader import *
import trading_clock as tc
from datetime import datetime, date, time, timedelta


# TODO: get trades from a text file


datetime_range = [tc.localize(datetime(2023, 6, 14, 9, 30, 0)),
                  tc.localize(datetime(2023, 6, 14, 16, 0, 0))]

start = datetime_range[0]
end = datetime_range[1]
this_generator = tc.get_generator([start, end])

spx_data = SecurityData(security=security)
for simulated_time in this_generator:
    tc.override(simulated_time)
    current_time = tc.get_today()

    if (current_time.minute % INTERVAL) == 0:
        spx_data.get_day_data("todaysData", current_time,
                            interval=INTERVAL, delta=0)
