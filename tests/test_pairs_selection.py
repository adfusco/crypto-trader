import numpy as np
import pandas as pd

from strategies.mean_reversion.mr_pairs import PairsMeanReversion


def _strategy(symbols):
    return PairsMeanReversion({
        'symbols': symbols, 'price_col': 'close', 'window': 20,
        'relationship': 'johansen',
    })


def test_select_universe_shortcuts_two_symbols():
    # with no real choice to make, the configured pair is returned as-is and no
    # screening runs (works even with no price data passed)
    strat = _strategy(['A/USDT', 'B/USDT'])
    assert strat.select_universe(pd.DataFrame()) == ['A/USDT', 'B/USDT']


def test_select_universe_picks_the_cointegrated_pair():
    rng = np.random.default_rng(0)
    n = 400
    common = np.cumsum(rng.normal(size=n)) + 100  # shared stochastic trend (I(1))
    df = pd.DataFrame({
        'timestamp': pd.date_range('2020-01-01', periods=n),
        'A_close': common + rng.normal(scale=0.5, size=n),
        'B_close': 2.0 * common + rng.normal(scale=0.5, size=n),  # cointegrated with A
        'C_close': np.cumsum(rng.normal(size=n)) + 100,           # independent walk
        'D_close': np.cumsum(rng.normal(size=n)) + 100,           # independent walk
    })
    strat = _strategy(['A/USDT', 'B/USDT', 'C/USDT', 'D/USDT'])
    # column names are symbol-prefixed; build the frame the walk-forward passes
    df = df.rename(columns={'A_close': 'A/USDT_close', 'B_close': 'B/USDT_close',
                            'C_close': 'C/USDT_close', 'D_close': 'D/USDT_close'})
    selected = strat.select_universe(df)
    assert set(selected) == {'A/USDT', 'B/USDT'}
