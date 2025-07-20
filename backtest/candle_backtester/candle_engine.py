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

    def run_backtest(self, price_col='close', start=None, end=None, closing_order_type='market'):
        start = start or self.df.iloc[0]['timestamp']
        end = end or self.df.iloc[-1]['timestamp']
        sliced = self.df.copy()
        sliced['timestamp'] = pd.to_datetime(sliced['timestamp'])
        sliced.set_index('timestamp', inplace=True)
        sliced = sliced[start:end]
        sliced.reset_index(inplace=True)

        for i in tqdm(range(0, len(sliced)), desc='backtesting'):
            row = sliced.iloc[i]

            if i < len(sliced)-1:
                self.strategy.update_state(row, self.portfolio.open_positions)
                signal = self.strategy.gen_signal()
                order_requests = self.strategy.gen_order(signal)
            else:
                order_requests = self._close_positions(closing_order_type)

            for order in order_requests:
                self.executor.execute_order(order, row)

            self.portfolio.mark_to_market(row, price_col, row['timestamp'])

    def _close_positions(self, closing_order_type):
        close_orders = []
        for symbol, pos in self.portfolio.open_positions.items():
            reverse_side = 'long' if pos['side'] == 'short' else 'short'
            reverse_qty = 1 if reverse_side == 'long' else -1
            order_type = closing_order_type

            close_order = {
            'symbol':symbol,
            'side':reverse_side,
            'qty':reverse_qty,
            'order_type':order_type,
        }
            close_orders.append(close_order)

        return close_orders
