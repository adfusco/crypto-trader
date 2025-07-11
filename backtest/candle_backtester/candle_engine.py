class Backtester:
    def __init__(self, strategy, executor, simulator, portfolio, logger, candle_df,):
        self.strategy = strategy
        self.executor = executor
        self.simulator = simulator
        self.portfolio = portfolio
        self.logger = logger
        self.data = candle_df

    def run_backtest(self, start_index=0, end_index=None):
        if end_index is None: end_index = len(self.data)
        self.data = self.data[(self.data['timestamp'] >= start_index) & (self.data['timestamp'] <= end_index)].copy()

        for i in range(0, len(self.data)):
            row = self.data.iloc[i]

            self.portfolio.mark_to_market(row)

            self.strategy.update_state(row)
            signal = self.strategy.gen_signal()
            order_request = self.strategy.gen_order(signal)

            self.executor.execute_order(order_request)