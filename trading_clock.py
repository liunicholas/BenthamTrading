from datetime import datetime, date, time, timedelta
import pytz

new_york_tz = pytz.timezone('America/New_York')

def localize(dt):
    return new_york_tz.localize(dt)

exchange_openclose = {
    "^spx": [time(hour=9, minute=30), time(hour=16)], 
    "^ixic": [time(hour=9, minute=30), time(hour=16)],
    }

# default variables
OVERRIDE = False
OVERRIDE_TIME = localize(datetime(year=2023, month=6, day=8,
                         hour=10, minute=59))
GENERATOR_RANGE = [localize(datetime(2023, 6, 8, 6, 30, 0)),
                   localize(datetime(2023, 6, 8, 23, 0, 0))]

def override(ot=OVERRIDE_TIME, VERBOSE=True):
    global OVERRIDE, OVERRIDE_TIME

    OVERRIDE = True
    OVERRIDE_TIME = ot
    
    if VERBOSE:
        print(f"Time Overridden to {OVERRIDE_TIME}")

def turn_off_override():
    global OVERRIDE
    OVERRIDE = False

    print("OVERRIDE is now False")

def get_generator(gt=GENERATOR_RANGE):
    global GENERATOR_RANGE

    GENERATOR_RANGE = gt

    print(f"Genrator Set from {GENERATOR_RANGE[0]} to {GENERATOR_RANGE[1]}")

    current_datetime = GENERATOR_RANGE[0]

    while current_datetime <= GENERATOR_RANGE[1]:
        yield current_datetime
        current_datetime += timedelta(minutes=1)

    print("Generator Done")

def get_today():
    if OVERRIDE:
        return OVERRIDE_TIME
    else:
        today = datetime.now(new_york_tz)
        return today

def real_time():
    # NO OVERRIDE
    return datetime.now(new_york_tz)


def is_market_open(security="^spx", current_datetime=get_today(), VERBOSE=False):
    if VERBOSE:
        print(f"[INFO] Checking time {current_datetime} for market open")

    holidays = [datetime(2023, 6, 19).date(), datetime(2023, 7, 4).date(),
                datetime(2023, 9, 4).date(), datetime(2023, 10, 9).date(),
                datetime(2023, 11, 11).date(), datetime(2023, 11, 23).date(),
                datetime(2023, 12, 25).date()]
    
    start_time = exchange_openclose[security][0]
    end_time = exchange_openclose[security][1]

    current_time = current_datetime.time()
    current_date = current_datetime.date()
    
    is_tradinghour = start_time <= current_time <= end_time
    is_weekend = current_date.weekday() >= 5
    is_holiday = current_date in holidays

    return is_tradinghour and not is_weekend and not is_holiday

def get_last_trading_date(security, date):
    lastTradingDay = localize(datetime.combine(date-timedelta(days=1), time(9, 35, 0)))

    while not is_market_open(security, lastTradingDay):
        lastTradingDay -= timedelta(days=1)
    
    return lastTradingDay.date()

def get_next_trading_date(security, date):
    TradingDay = localize(datetime.combine(date+timedelta(days=1), time(9, 35, 0)))

    while not is_market_open(security, TradingDay):
        TradingDay += timedelta(days=1)
    
    return TradingDay.date()

def get_delta_trading_date(security, date, delta):
    if delta > 0:
        for _ in range(delta):
            date = get_next_trading_date(security, date)
    elif delta < 0:
        for _ in range(-1*delta):
            date = get_last_trading_date(security, date)
    else:
        date = date
    
    return date
    
def datetime_is_between(t, start_time, end_time):
    return parse_hour_minute(start_time) <= t.time() <= parse_hour_minute(end_time)

def parse_hour_minute(stringTime):
    splitTime = stringTime.split(":")
    return time(hour=int(splitTime[0]), minute=int(splitTime[1]))

if __name__ == "__main__":
    print(datetime_is_between(datetime.now(new_york_tz), "4:00", "5:00"))