from datetime import datetime, time, timedelta, date
import pytz

new_york_tz = pytz.timezone('America/New_York')
exchange_openclose = {"^spx": [time(hour=9, minute=30), time(hour=16)], }

OVERRIDE = True
OVERRIDE_TIME = datetime(year=2023, month=6, day=8, hour=10, minute=59)

def get_today():
    today = datetime.now(new_york_tz)

    if OVERRIDE:
        today = OVERRIDE_TIME
    
    return today

def time_during_day(datetime, time):
    return datetime.combine(datetime.date(), parse_hour_minute(time)).astimezone(new_york_tz)

def is_market_open(security):
    holidays = [datetime(2023, 6, 16).date(), datetime(2023, 7, 4).date(),
                datetime(2023, 9, 4).date(), datetime(2023, 10, 9).date(),
                datetime(2023, 11, 11).date(), datetime(2023, 11, 23).date(),
                datetime(2023, 12, 25).date()]
    
    start_time = exchange_openclose[security][0]
    end_time = exchange_openclose[security][1]
    # current = datetime.now(new_york_tz)
    current = get_today()

    current_time = current.time()
    current_date = current.date()
    
    is_tradinghour = start_time <= current_time <= end_time
    is_weekend = current_date.weekday() >= 5
    is_holiday = current.date() in holidays

    return is_tradinghour and not is_weekend and not is_holiday

def datetime_is_between(t, start_time, end_time):
    return parse_hour_minute(start_time) <= t.time() <= parse_hour_minute(end_time)

def parse_hour_minute(stringTime):
    splitTime = stringTime.split(":")
    return time(hour=int(splitTime[0]), minute=int(splitTime[1]))

if __name__ == "__main__":
    print(datetime_is_between(datetime.now(new_york_tz), "4:00", "5:00"))