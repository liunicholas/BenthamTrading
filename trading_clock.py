from datetime import datetime, time, timedelta, date
import pytz

new_york_tz = pytz.timezone('America/New_York')
exchange_openclose = {
    "^SPX": [time(hour=9, minute=30), time(hour=16)], }

OVERRIDE = False
OVERRIDE_TIME = datetime(year=2023, month=6, day=8, hour=9, minute=30)


def get_today(today=datetime.now(new_york_tz).date()):
    year = today.year
    month = today.month
    day = today.day

    return year, month, day


def get_yesterday(today=datetime.now(new_york_tz).date()):
    yesterday = today - timedelta(days=1)

    year = yesterday.year
    month = yesterday.month
    day = yesterday.day

    return year, month, day


def get_tomorrow(today=datetime.now(new_york_tz).date()):
    tomorrow = today + timedelta(days=1)

    year = tomorrow.year
    month = tomorrow.month
    day = tomorrow.day

    return year, month, day

def is_market_open(derivative):
    holidays = [datetime(2023, 6, 16).date(), datetime(2023, 7, 4).date(),
                datetime(2023, 9, 4).date(), datetime(2023, 10, 9).date(),
                datetime(2023, 11, 11).date(), datetime(2023, 11, 23).date(),
                datetime(2023, 12, 25).date()]
    
    start_time = exchange_openclose[derivative][0]
    end_time = exchange_openclose[derivative][1]
    current = datetime.now(new_york_tz)
    
    if OVERRIDE:
        current = OVERRIDE_TIME

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