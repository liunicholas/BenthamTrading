from datetime import datetime, date, time, timedelta
import pytz

new_york_tz = pytz.timezone('America/New_York')

exchange_openclose = {
    "ETF": [time(hour=9, minute=30), time(hour=16)],
}

def localize(dt):
    return new_york_tz.localize(dt)

def tz_to_ny(dt):
    return dt.astimezone(new_york_tz)

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
        return tz_to_ny(datetime.now())

def real_time():
    # NO OVERRIDE
    return tz_to_ny(datetime.now())

def is_market_open(security_type, current_datetime, VERBOSE=False):
    if VERBOSE:
        print(f"[INFO] Checking time {current_datetime} for market open")

    if security_type == "ETF":
        holidays = [date(2023, 6, 19), date(2023, 7, 4),
                    date(2023, 9, 4), date(2023, 10, 9),
                    date(2023, 11, 11), date(2023, 11, 23),
                    date(2023, 12, 25)]
        
        start_time = exchange_openclose["ETF"][0]
        end_time = exchange_openclose["ETF"][1]

        current_time = current_datetime.time()
        current_date = current_datetime.date()
        
        is_tradinghour = start_time <= current_time <= end_time
        is_weekend = current_date.weekday() >= 5
        is_holiday = current_date in holidays

        return is_tradinghour and not is_weekend and not is_holiday
    
    elif security_type == "CFD":
        print("[ERROR] Not Implemented Yet")
        pass
    elif security_type == "FUTURES":
        print("[ERROR] Not Implemented Yet")
        pass
    else:
        print("[ERROR] Market Times Not Available")

def get_last_trading_date(security_type, date):
    lastTradingDay = localize(datetime.combine(date-timedelta(days=1), time(9, 35, 0)))

    while not is_market_open(security_type, lastTradingDay):
        lastTradingDay -= timedelta(days=1)
    
    return lastTradingDay.date()

def get_next_trading_date(security_type, date):
    TradingDay = localize(datetime.combine(date+timedelta(days=1), time(9, 35, 0)))

    while not is_market_open(security_type, TradingDay):
        TradingDay += timedelta(days=1)
    
    return TradingDay.date()

def get_delta_trading_date(security_type, date, delta):
    if delta > 0:
        for _ in range(delta):
            date = get_next_trading_date(security_type, date)
    elif delta < 0:
        for _ in range(-delta):
            date = get_last_trading_date(security_type, date)
    else:
        date = date
    
    return date

def get_trading_days_between(security_type, start, end):
    days = 0
    current_index = start
    while current_index < end:
        days += 1
        current_index = get_next_trading_date(security_type, current_index)

    return days
    
def datetime_is_between(t, start_time, end_time):
    return parse_hour_minute(start_time) <= t.time() <= parse_hour_minute(end_time)

def parse_hour_minute(stringTime):
    splitTime = stringTime.split(":")
    return time(hour=int(splitTime[0]), minute=int(splitTime[1]))

if __name__ == "__main__":
    print(datetime_is_between(real_time(), "4:00", "5:00"))