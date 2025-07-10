import pandas as pd

from data_ingestion.fetch_ohlcv import fetch_symbols_ohlcv
from feature_engineering.rolling_features import add_rolling_features

from strategies.mean_reversion.mean_reversion_basic import MeanReversionBasic
from backtest.candle_backtester.candle_engine import run_backtest
from backtest.candle_backtester.candle_portfolio import Portfolio
from backtest.candle_backtester.candle_logger import Logger
#from backtest.candle_backtester.candle_metrics import

#define strategy
use_precomputed_features = True
window = 20
price_col_name = 'close'
zscores = {
    'long_entry':-1,
    'long_exit':-1,
    'short_entry':1,
    'short_exit':1
}
strategy_params = {
    'use_precomputed_features':use_precomputed_features,
    'window':window,
    'price_col':price_col_name,
    'zscores':zscores
}
strategy = MeanReversionBasic(strategy_params)


#prepare data
candle_df = pd.read_csv('./data_ingestion/data/BTC_USDT.csv')

if use_precomputed_features:
    required_features = strategy.required_features
    candle_df = add_rolling_features(candle_df, required_features)


#define portfolio and logger

portfolio_params = {}
portfolio = Portfolio()

logger = Logger()


#run strategy
run_backtest(strategy, candle_df, portfolio, logger)


#run metrics