import pandas as pd

from strategies.base import Strategy
from backtest.engine import Backtester
from backtest.executor import DummyExecutor
from backtest.simulator import DummySimulator
from backtest.portfolio import Portfolio
from backtest.logger import NullLogger

SYMBOL = 'X/USDT'


class BuyOnceStrategy(Strategy):
    """Emits a single long signal on the first bar, holds thereafter."""
    def __init__(self, params):
        super().__init__(params)
        self.bars_seen = 0
        self._buy = False

    def update_state(self, row, open_positions=None):
        self._buy = (self.bars_seen == 0)
        self.bars_seen += 1

    def gen_signal(self):
        return {'side': 'long', 'order_type': 'market'} if self._buy else {'side': 'hold'}

    def gen_order(self, signal, row, portfolio):
        if signal['side'] == 'hold':
            return {}
        return {SYMBOL: {'side': 'long', 'qty': 1, 'order_type': 'market'}}


def _df():
    return pd.DataFrame({
        'timestamp': ['2022-01-01', '2022-01-02', '2022-01-03'],
        f'{SYMBOL}_open': [10.0, 20.0, 30.0],
        f'{SYMBOL}_close': [15.0, 25.0, 35.0],
    })


def _run():
    portfolio = Portfolio(NullLogger(), init_cash=100000.0)
    simulator = DummySimulator(slippage_bps=0, fee_rate=0.0)
    executor = DummyExecutor(portfolio, simulator)
    strategy = BuyOnceStrategy({'symbol': SYMBOL})
    Backtester(strategy, executor, simulator, portfolio, NullLogger(), _df()).run_backtest(price_col='close')
    return portfolio


def test_signal_fills_on_next_bar_open_not_current():
    p = _run()
    # bar-0 signal must NOT fill at bar-0 open (10); it fills at bar-1 open (20)
    entry = p.fill_log[0]
    assert entry['execution_price'] == 20.0
    assert entry['timestamp'] == pd.Timestamp('2022-01-02')


def test_final_bar_flattens_position():
    p = _run()
    # close order executes on the last bar at its open (30)
    assert SYMBOL not in p.open_positions
    assert p.fill_log[-1]['execution_price'] == 30.0
