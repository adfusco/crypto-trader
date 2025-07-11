import pandas as pd

from data_ingestion.fetch_ohlcv import fetch_symbols_ohlcv
from feature_engineering.rolling_features import add_rolling_features

from strategies.mean_reversion.mean_reversion_basic import MeanReversionBasic
from backtest.candle_backtester.candle_engine import Backtester
from backtest.candle_backtester.candle_executor import DummyExecutor
from backtest.candle_backtester.candle_simulator import DummySimulator
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


#define backtesting classes
portfolio = Portfolio()
simulator = DummySimulator()
executor = DummyExecutor(portfolio, simulator)
logger = Logger()
backtester = Backtester(strategy, executor, simulator, portfolio, logger, candle_df)

#run strategy



#run metrics