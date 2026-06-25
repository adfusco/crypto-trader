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

        # Signals generated on bar i are queued and filled at bar i+1's open (no lookahead).
        pending_orders = {}
        for i in tqdm(range(0, len(sliced)), desc='backtesting'):
            row = sliced.iloc[i]

            self.executor.execute_orders(pending_orders, row)
            self.portfolio.mark_to_market(row, price_col, row['timestamp'])

            if i < len(sliced) - 1:
                self.strategy.update_state(row, self.portfolio.open_positions)
                signal = self.strategy.gen_signal()
                pending_orders = self.strategy.gen_order(signal, row, self.portfolio)
            else:
                close_orders = self._close_positions(closing_order_type)
                self.executor.execute_orders(close_orders, row)
                pending_orders = {}

        self.logger.flush_all()

    def _close_positions(self, closing_order_type):
        close_orders = {}
        for symbol, pos in self.portfolio.open_positions.items():
            reverse_side = 'long' if pos['side'] == 'short' else 'short'
            close_order = {
                'side': reverse_side,
                'qty': abs(pos['qty']),
                'order_type': closing_order_type
            }
            close_orders[symbol] = close_order

        return close_orders
