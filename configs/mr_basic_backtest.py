config = {
    'mode': 'backtest',
    'strategy': 'mr_basic',
    'strategy_params': {
        'use_precomputed_features': True,
        'symbol': 'ETH/USDT',
        'window': 40,
        'price_col': 'close',
        'risk_pct': 0.02,
        'zscores': {'long_entry': -1, 'long_exit': -1, 'short_entry': 1, 'short_exit': 1},
    },
    'symbols': ['ETH/USDT'],
    'timeframe': '1d',
    'start': '2022-01-01',   # bounds both the fetch range and the backtest slice
    'end': None,             # None = up to latest available
    'init_cash': 100000.0,
    'slippage_bps': 5,
}
