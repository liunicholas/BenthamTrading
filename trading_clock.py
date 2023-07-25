from datetime import datetime, date, time, timedelta
import pytz

new_york_tz = pytz.timezone('America/New_York')

NYSE_open = time(hour=9, minute=30)
NYSE_close = time(hour=16)

# 0 is Monday
exchange_openclose = {
    "ETF": {
        0: [(time(hour=9, minute=30), time(hour=16))],
        1: [(time(hour=9, minute=30), time(hour=16))],
        2: [(time(hour=9, minute=30), time(hour=16))],
        3: [(time(hour=9, minute=30), time(hour=16))],
        4: [(time(hour=9, minute=30), time(hour=16))],
        5: "CLOSED",
        6: "CLOSED",
    },
    "CFD": {
        0: [(time(hour=0), time(hour=23,minute=59,second=59))],
        1: [(time(hour=0), time(hour=23, minute=59, second=59))],
        2: [(time(hour=0), time(hour=23, minute=59, second=59))],
        3: [(time(hour=0), time(hour=23, minute=59, second=59))],
        4: [(time(hour=0), time(hour=17))],
        5: "CLOSED",
        6: [(time(hour=17), time(hour=23, minute=59, second=59))],
    },
    "FUTURES": {
        0: [(time(hour=0), time(hour=17)), (time(hour=18), time(hour=23, minute=59, second=59))],
        1: [(time(hour=0), time(hour=17)), (time(hour=18), time(hour=23, minute=59, second=59))],
        2: [(time(hour=0), time(hour=17)), (time(hour=18), time(hour=23, minute=59, second=59))],
        3: [(time(hour=0), time(hour=17)), (time(hour=18), time(hour=23, minute=59, second=59))],
        4: [(time(hour=0), time(hour=17))],
        5: "CLOSED",
        6: [(time(hour=18), time(hour=23, minute=59, second=59))],
    },
}

federal_holidays = {"new_years": date(2023, 1, 2),
                    "mlk": date(2023, 1, 16),
                    "washington": date(2023, 2, 20),
                    "memorial": date(2023, 5, 29),
                    "juneteenth": date(2023, 6, 19),
                    "independence": date(2023, 7, 4),
                    "labor": date(2023, 9, 4),
                    "columbus": date(2023, 10, 9),
                    "veterans": date(2023, 11, 11),
                    "thanksgiving": date(2023, 11, 23),
                    "christmas": date(2023, 12, 25)}

half_day_before = [federal_holidays["independence"]-timedelta(days=1),
                   federal_holidays["christmas"]-timedelta(days=1)]

half_day_after = [federal_holidays["thanksgiving"]+timedelta(days=1)]

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

def get_generator(gt=GENERATOR_RANGE, INTERVAL=5):
    global GENERATOR_RANGE

    GENERATOR_RANGE = gt

    print(f"Genrator Set from {GENERATOR_RANGE[0]} to {GENERATOR_RANGE[1]}")

    current_datetime = GENERATOR_RANGE[0]

    while current_datetime <= GENERATOR_RANGE[1]:
        yield current_datetime
        current_datetime += timedelta(minutes=INTERVAL)

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
        print(f"[INFO] Checking time {current_datetime} for market open for {security_type}")

    current_time = current_datetime.time()
    current_date = current_datetime.date()

    if security_type in exchange_openclose.keys():
        this_security_market_times = exchange_openclose[security_type]
        day_of_week = current_datetime.weekday()
        this_day_times = this_security_market_times[day_of_week]

        is_holiday = current_date in federal_holidays.values()
        if this_day_times == "CLOSED" or is_holiday:
            return False
        else:
            for open_close_pair in this_day_times:
                if open_close_pair[0] <= current_time <= open_close_pair[1]:
                    return True
                
            return False
        
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

def last_five_minute(t):
    multiple = (t.minute // 5)
    return localize(datetime.combine(t.date(), time(t.hour, multiple*5, 0)))

def next_five_minute(t):
    multiple = (t.minute // 5) + 1
    if multiple == 12:
        return localize(datetime.combine(t.date(), time(t.hour+1, 0, 0)))
    else:
        return localize(datetime.combine(t.date(), time(t.hour, multiple*5, 0)))

if __name__ == "__main__":
    print(datetime_is_between(real_time(), "4:00", "5:00"))