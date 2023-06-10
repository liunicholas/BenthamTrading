class TradeOrder:
    def __init__(self, timeFound, entry, stop_limit, take_profit, position_size):
        self.time_found = timeFound
        self.entry = entry
        self.stop_limit = stop_limit
        self.take_profit = take_profit
        self.position_size = position_size

    def __str__(self):
        return f"TradeOrder - Time Found: {self.time_found}, Entry Price: {self.entry:0.2f}\n \
            Stop Limit: {self.stop_limit}, Take Profit: {self.take_profit}\n \
                Position Size: {self.position_size}\n\n"