import asyncio
import ccxt.async_support as ccxt
from datetime import datetime, timezone
import pickle

from data_ingestion.fetch_ohlcv import fetch_symbols_ohlcv
from data_ingestion.prepare_data import prepare_candle_data

from strategies.mean_reversion.mean_reversion_basic import MeanReversionBasic
from backtest.candle_backtester.candle_engine import Backtester
from backtest.candle_backtester.candle_executor import DummyExecutor
from backtest.candle_backtester.candle_simulator import DummySimulator
from backtest.candle_backtester.candle_portfolio import Portfolio
from backtest.candle_backtester.candle_logger import Logger

#define strategy
use_precomputed_features = True
window = 40
symbol = 'ETH/USDT'
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

#prepare raw_csvs
year, month, day = 2022, 1, 1
dt = datetime(year, month, day, tzinfo=timezone.utc)

exchange = ccxt.mexc()
symbols = [symbol]
timeframe = '1d'
since_ms = int(dt.timestamp() * 1000)
limit = 1000
path_to_csvs = 'data_ingestion/raw_csvs'

fetch_params = {
    'exchange':exchange,
    'symbols':symbols,
    'timeframe':timeframe,
    'limit':limit,
    'since':since_ms,
    'save_dir':path_to_csvs
}

async def main():
    try: await fetch_symbols_ohlcv(**fetch_params)
    finally: await exchange.close()
asyncio.run(main())

features = strategy.required_features
path_to_merged_data = 'data_ingestion/clean_data/backtest'
candle_df = prepare_candle_data(symbols, use_precomputed_features, features, path_to_csvs, path_to_merged_data)

#define backtesting classes
logger = Logger(base_path='logs/dummy_test')
portfolio = Portfolio(logger, init_cash=100000.0)
simulator = DummySimulator(slippage_bps=5)
executor = DummyExecutor(portfolio, simulator)
backtester = Backtester(strategy, executor, simulator, portfolio, logger, candle_df)

#run strategy
backtester.run_backtest()

#save portfolio information for metrics and visualizations
portfolio_data = {
    'timeframe':timeframe,
    'timestamps':portfolio.timestamps,
    'equity_curve':portfolio.equity_curve,
    'max_equity':portfolio.max_equity,
    'drawdowns':portfolio.drawdowns,
    'max_drawdown_amt':portfolio.max_drawdown_amt,
    'max_drawdown_pct':portfolio.max_drawdown_pct,
    'trade_history':portfolio.trade_history,
    'total_fees':portfolio.total_fees
}
portfolio_name = strategy.__class__.__name__
portfolio_path = 'metrics/portfolio_data/' + portfolio_name + '.pkl'

with open(portfolio_path, 'wb') as f:
    pickle.dump(portfolio_data, f)