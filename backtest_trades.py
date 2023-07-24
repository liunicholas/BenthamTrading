from trader import *

month = 7
day = 19
test_date_start = tc.localize(datetime(2023, month, day, 9, 30, 0))
test_date_end = tc.localize(datetime(2023, month, day, 16, 0, 0))
for i in range(1):
    # override time so the log file is written correctly
    tc.override(test_date_start)
    snp_silver_bullet = SilverBullet(
        security="spxFUTURES", security_type="ETF", 
        take_profit_margin=10, stop_loss_margin=3, leverage_multiplier=5, 
        OVERRIDE=True)
    snp_silver_bullet.simulate_cycles(
        start_time=test_date_start, end_time=test_date_end)

    tc.override(test_date_start)
    ndq_silver_bullet = SilverBullet(
        security="ndqFUTURES", security_type="ETF", 
        take_profit_margin=30, stop_loss_margin=10, leverage_multiplier=2,
        OVERRIDE=True)
    ndq_silver_bullet.simulate_cycles(
        start_time=test_date_start, end_time=test_date_end)

    test_date_start = tc.localize(datetime.combine(
        tc.get_last_trading_date("ETF", test_date_start), time(9, 30, 0)))
    
    test_date_end = tc.localize(datetime.combine(
        tc.get_last_trading_date("ETF", test_date_end), time(16, 0, 0)))
