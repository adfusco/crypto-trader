# Walk-forward pair *selection*: instead of hand-picking one cointegrated pair
# (which leaks the test window into the choice), give the walk-forward a universe
# and let it screen each fold's TRAIN window and trade the top cointegrated pair.
# Pair choice, hedge ratio, and trading rule are all fit train-only -> no selection
# bias. The pair can change fold to fold; a fold with no cointegrated pair sits out.
#
# Compare against mr_pairs_walkforward (fixed DOT/XTZ) to see what honest, blind
# pair selection costs versus a pair we already knew survived in-sample.

_universe = ['DOT/USDT', 'XTZ/USDT', 'LINK/USDT', 'ADA/USDT', 'ATOM/USDT', 'LTC/USDT']

config = {
    'mode': 'walkforward',
    'strategy': 'mr_pairs',
    'objective': 'sharpe',

    'base_params': {
        'use_precomputed_features': True,
        'symbols': _universe,         # the candidate universe; the traded pair is chosen per fold
        'hedge_ratio': 1.0,           # placeholder; re-fit per fold on the selected pair
        'relationship': 'johansen',   # used for both pair selection (screen) and beta (estimate)
        'selection': None,            # None -> reuse 'relationship' as the screener
        'window': 40,
        'price_col': 'close',
        'risk_pct': 0.02,
        'zscores': {'long_entry': -1, 'long_exit': 0, 'short_entry': 1, 'short_exit': 0},
    },
    'param_grid': {
        'zscores': [
            {'long_entry': -1.0, 'long_exit': 0.0, 'short_entry': 1.0, 'short_exit': 0.0},
            {'long_entry': -1.5, 'long_exit': 0.0, 'short_entry': 1.5, 'short_exit': 0.0},
            {'long_entry': -2.0, 'long_exit': 0.0, 'short_entry': 2.0, 'short_exit': 0.0},
        ],
        'risk_pct': [0.02, 0.05],
    },

    'symbols': _universe,
    'timeframe': '1d',
    'init_cash': 100000.0,
    'slippage_bps': 5,

    'train_size': 365,
    'test_size': 90,
    'step': 90,

    'start': '2020-09-01',   # DOT lists 2020-08-22; first train window starts here
    'end': None,
}
