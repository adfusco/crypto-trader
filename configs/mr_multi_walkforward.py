config = {
    'mode': 'walkforward',
    'strategy': 'mr_multi',
    'objective': 'sharpe',

    # fixed across folds: feature window is precomputed once on the full series
    'base_params': {
        'use_precomputed_features': True,
        'symbols': ['ETH/USDT', 'SOL/USDT'],
        'window': 40,
        'price_col': 'close',
        'risk_pct': 0.02,
        'zscores': {'long_entry': -1, 'long_exit': -1, 'short_entry': 1, 'short_exit': 1},
    },
    # searched on each train window: the trading rule, not the feature window
    'param_grid': {
        'zscores': [
            {'long_entry': -1.0, 'long_exit': 0.0, 'short_entry': 1.0, 'short_exit': 0.0},
            {'long_entry': -1.5, 'long_exit': 0.0, 'short_entry': 1.5, 'short_exit': 0.0},
            {'long_entry': -2.0, 'long_exit': 0.0, 'short_entry': 2.0, 'short_exit': 0.0},
        ],
        'risk_pct': [0.02, 0.05],
    },

    'symbols': ['ETH/USDT', 'SOL/USDT'],
    'timeframe': '1d',
    'init_cash': 100000.0,
    'slippage_bps': 5,

    # rolling window sizes (bars). ~960 daily bars -> ~6 folds.
    'train_size': 365,
    'test_size': 90,
    'step': 90,

    'start': '2022-01-01',   # bounds the fold universe
    'end': None,
}
