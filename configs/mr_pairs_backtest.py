from asset_analysis.analysis_engine import estimate_pair

_symbols = ['ETH/USDT', 'SOL/USDT']
_path_to_csvs = 'data_ingestion/raw_csvs'

# hedge ratio for the spread A - beta*B, via the named relationship estimator
_hedge_ratio, _meta = estimate_pair(_symbols, 'close', _path_to_csvs, method='johansen')
if not _meta.get('cointegrated', True):
    print(f'WARNING: {_symbols} not cointegrated at 5%. Pairs result is not statistically valid.')

config = {
    'mode': 'backtest',
    'strategy': 'mr_pairs',
    'strategy_params': {
        'use_precomputed_features': True,
        'symbols': _symbols,
        'hedge_ratio': _hedge_ratio,
        'window': 40,
        'price_col': 'close',
        'risk_pct': 0.02,
        'zscores': {'long_entry': -1, 'long_exit': 0, 'short_entry': 1, 'short_exit': 0},
    },
    'symbols': _symbols,
    'timeframe': '1d',
    'start': '2022-01-01',
    'end': None,
    'init_cash': 100000.0,
    'slippage_bps': 5,
}
