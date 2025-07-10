from data_ingestion.fetch_ohlcv import fetch_symbols_ohlcv
from feature_engineering.rolling_features import add_rolling_features

from backtest.candle_backtester.candle_portfolio import Portfolio
from strategies.mean_reversion.mean_reversion_basic import MeanReversionBasic
from backtest.candle_backtester.candle_engine import run_backtest


strategy_params = {
    ''
}
strategy = MeanReversionBasic()

use_precomputed_features = True

if use_precomputed_features:
    required_features = strategy.params['required_features']
    candle_df = add_rolling_features(candle_df, required_features)
