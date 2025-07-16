import pandas as pd
from tqdm import tqdm

class Backtester:
    def __init__(self, strategy, executor, simulator, portfolio, logger, candle_df):
        self.strategy = strategy
        self.executor = executor
        self.simulator = simulator
        self.portfolio = portfolio
        self.logger = logger
        self.df = candle_df

    def run_backtest(self, price_col='close', start=None, end=None):
        start = start or self.df.iloc[0]['timestamp']
        end = end or self.df.iloc[-1]['timestamp']
        sliced = self.df.copy()
        sliced['timestamp'] = pd.to_datetime(sliced['timestamp'])
        sliced.set_index('timestamp', inplace=True)
        sliced = sliced[start:end]
        sliced.reset_index(inplace=True)

        for i in tqdm(range(0, len(sliced)), desc='backtesting'):
            row = sliced.iloc[i]

            self.portfolio.mark_to_market(row, price_col, row['timestamp'])
            self.strategy.update_state(row, self.portfolio.open_positions)
            signal = self.strategy.gen_signal()
            order_request = self.strategy.gen_order(signal)

            self.executor.execute_order(order_request, row)