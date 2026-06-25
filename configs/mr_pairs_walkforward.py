from asset_analysis.analysis_engine import estimate_pair

_symbols = ['DOT/USDT', 'XTZ/USDT']
_path_to_csvs = 'data_ingestion/raw_csvs'

# Walk-forward re-fits the hedge ratio on each fold's train window (see
# PairsMeanReversion.fit_fold_params), so this full-sample beta is only a fallback
# used to confirm the pair is cointegrated before running.
_hedge_ratio, _meta = estimate_pair(_symbols, 'close', _path_to_csvs, method='johansen')
print(f'DOT/XTZ full-sample hedge_ratio={_hedge_ratio:.4f}, cointegrated={_meta.get("cointegrated")}')

config = {
    'mode': 'walkforward',
    'strategy': 'mr_pairs',
    'objective': 'sharpe',

    'base_params': {
        'use_precomputed_features': True,
        'symbols': _symbols,
        'hedge_ratio': _hedge_ratio,
        'relationship': 'johansen',  # estimator re-fit per fold; try 'ols' to compare
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

    'symbols': _symbols,
    'timeframe': '1d',
    'init_cash': 100000.0,
    'slippage_bps': 5,

    # ~1900 daily bars -> roughly 17 folds
    'train_size': 365,
    'test_size': 90,
    'step': 90,

    'start': '2020-01-01',   # DOT/XTZ listed ~2020; bounds the fold universe
    'end': None,
}
