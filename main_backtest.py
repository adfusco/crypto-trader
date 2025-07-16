import asyncio
import ccxt.async_support as ccxt

from data_ingestion.fetch_ohlcv import fetch_symbols_ohlcv
from data_ingestion.prepare_data import prepare_candle_data

from strategies.mean_reversion.mean_reversion_basic import MeanReversionBasic
from backtest.candle_backtester.candle_engine import Backtester
from backtest.candle_backtester.candle_executor import DummyExecutor
from backtest.candle_backtester.candle_simulator import DummySimulator
from backtest.candle_backtester.candle_portfolio import Portfolio
from backtest.candle_backtester.candle_logger import Logger
from backtest.candle_backtester.candle_metrics import Metrics

#define strategy
use_precomputed_features = True
window = 20
symbol = 'BTC/USDT'
price_col_name = 'close'
zscores = {
    'long_entry':-1,
    'long_exit':-1,
    'short_entry':1,
    'short_exit':1
}
strategy_params = {
    'use_precomputed_features':use_precomputed_features,
    'symbol':symbol,
    'window':window,
    'price_col':price_col_name,
    'zscores':zscores
}
strategy = MeanReversionBasic(strategy_params)

#prepare data
exchange = ccxt.mexc()
symbols = [symbol]
features = strategy.required_features
timeframe = '1d'
limit = 600
path_to_csvs = 'data_ingestion/data'
path_to_merged_data = 'data_ingestion/clean_data'

async def main():
    try: await fetch_symbols_ohlcv(exchange, symbols, timeframe, limit, path_to_csvs)
    finally: await exchange.close()
asyncio.run(main())

candle_df = prepare_candle_data(symbols, use_precomputed_features, features, path_to_csvs, path_to_merged_data)

#define backtesting classes
logger = Logger(base_path='logs/dummy_test')
portfolio = Portfolio(logger, init_cash=1000000.0)
simulator = DummySimulator()
executor = DummyExecutor(portfolio, simulator)
backtester = Backtester(strategy, executor, simulator, portfolio, logger, candle_df)

#run strategy
backtester.run_backtest()

#run metrics
metrics = Metrics(portfolio)

print(metrics.compute_stats())
print(metrics.return_basic_stats())
print(portfolio.trade_history)

import matplotlib.pyplot as plt

plt.plot(metrics.equity_curve.index, metrics.equity_curve['equity'])
plt.show()