import trading_clock as tc
from silver_bullet import *

def managePortfolio(candidate_trades):
    pass
    
def run_day():
    snp_silver_bullet = SilverBullet(
        security="^spx", take_profit_margin=10, stop_loss_margin=3)
    ndq_silver_bullet = SilverBullet(
        security="^ixic", take_profit_margin=30, stop_loss_margin=10)

    last_known_minute = -1
    while tc.is_market_open(current_datetime=tc.get_today()):
        # run cycles once a minute
        current_time = tc.get_today()
        if current_time.minute != last_known_minute:
            last_known_minute = current_time.minute

            snp_silver_bullet.run_cycle(current_time)
            ndq_silver_bullet.run_cycle(current_time)

            # check on portfolio every iteration
            managePortfolio([
                snp_silver_bullet.candidate_trades, 
                ndq_silver_bullet.candidate_trades,])

    return

def main():
    LIVE = True
    last_known_minute = -1
    while LIVE:
        # tc.override(tc.localize(datetime(year=2023, month=6, day=22, hour=16, minute=00)))
        current_time = tc.get_today()
        if current_time.minute != last_known_minute:
            last_known_minute = current_time.minute

            if tc.is_market_open(current_datetime=current_time, VERBOSE=True):
                print("MARKET OPENED")
                run_day()

            else:
                print("MARKET CLOSED")

if __name__ == "__main__":
    main()