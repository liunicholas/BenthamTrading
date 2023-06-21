class TradeOrder:
    def __init__(self, time_found, entry, stop_limit, take_profit, position_size, trade_type, leverage):
        self.time_found = time_found
        self.entry = entry
        self.stop_limit = stop_limit
        self.take_profit = take_profit
        self.position_size = position_size
        self.trade_type = trade_type
        self.leverage = leverage
        
        self.entry_time = None
        self.position_opened = False
        self.position_closed = False

    def __str__(self):
        return f"\n[TRADE ORDER]: \n \
        Type: {self.trade_type}, \n \
        Time Found: {self.time_found}, \n \
        Entry Price: {self.entry:0.2f}, \n \
        Stop Limit: {self.stop_limit}, \n \
        Take Profit: {self.take_profit}, \n \
        Position Size: {self.position_size}, \n \
        Leverage Multiplier: {self.leverage}, \n"

class ExecutedTrade:
    def __init__(self, trade_order, exit_price, exit_time, exit_type):
        self.trade_order = trade_order
        self.entry_price = trade_order.entry
        self.entry_time = trade_order.entry_time
        self.position_size = trade_order.position_size
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.exit_type = exit_type

        if trade_order.trade_type == "LONG":
            self.pnl = (exit_price-trade_order.entry)*trade_order.leverage*trade_order.position_size
        if trade_order.trade_type == "SHORT":
            self.pnl = (trade_order.entry-exit_price) * trade_order.leverage*trade_order.position_size

    def __str__(self):
        return f"\n[EXECUTED TRADE]: \n \
        Exit Type: {self.exit_type}, \n \
        Trade Type: {self.trade_order.trade_type}, \n \
        Position Size: {self.position_size:0.2f}, \n \
        Entry Time: {self.entry_time}, \n \
        Entry Price: {self.entry_price:0.2f}, \n \
        Exit Time: {self.exit_time}, \n \
        Exit Price: {self.exit_price:0.2f}, \n \
        PNL: {self.pnl:0.2f}, \n"