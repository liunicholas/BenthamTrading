from trader import *

datetime_range = [tc.localize(datetime(2023, 6, 22, 9, 30, 0)),
                  tc.localize(datetime(2023, 6, 22, 16, 0, 0))]

tc.override(datetime_range[0])  # override time so the log file is written correctly
snp_silver_bullet = SilverBullet(
    security="^ixic", take_profit_margin=30, stop_loss_margin=10, OVERRIDE=True)

snp_silver_bullet.simulate_cycles(start_time=datetime_range[0], end_time=datetime_range[1])