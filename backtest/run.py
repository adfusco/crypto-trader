import os
import pickle

import pandas as pd

from data_ingestion.fetch_ohlcv import fetch_to_csvs
from data_ingestion.prepare_data import prepare_candle_data
from backtest.engine import Backtester
from backtest.executor import DummyExecutor
from backtest.simulator import DummySimulator
from backtest.portfolio import Portfolio
from backtest.logger import Logger, NullLogger


def apply_defaults(config):
    """Fill in plumbing paths so configs carry only real choices. Per-run paths
    derive from the unique config 'name' (no collisions between configs); shared
    locations get constant defaults. An explicit value in the config still wins."""
    name = config['name']
    config.setdefault('path_to_csvs', 'data_ingestion/raw_csvs')
    config.setdefault('portfolio_save_dir', 'metrics/portfolio_data')
    config.setdefault('path_to_merged_data', f'data_ingestion/clean_data/backtest/{name}.csv')
    config.setdefault('log_dir', f'logs/{name}')
    return config


def load_candle_data(config, required_features, required_multi_features, symbols=None):
    # symbols defaults to the configured set; walk-forward pair selection passes
    # the full universe to load (it picks the traded pair per fold from these).
    symbols = symbols or config['symbols']
    # fetch is opt-in: default False reuses cached CSVs. Set fetch=True (or pass
    # --fetch) to re-download before running.
    if config.get('fetch', False):
        fetch_to_csvs(symbols, config['timeframe'], config['start'],
                      config.get('end'), config['path_to_csvs'])
    # single-run configs carry 'strategy_params'; walk-forward carries 'base_params'
    params = config.get('strategy_params') or config['base_params']
    return prepare_candle_data(
        symbols,
        params['use_precomputed_features'],
        required_features,
        required_multi_features,
        config['path_to_csvs'],
        config['path_to_merged_data'],
        timeframe=config['timeframe'],
    )


def _benchmark_slice(candle_df, timestamps):
    # close-price slice for the buy-and-hold benchmark, trimmed to the bars the
    # run actually covered so a fold's benchmark is based on its own first bar.
    price_cols = ['timestamp'] + [c for c in candle_df.columns if c.endswith('_close')]
    prices = candle_df[price_cols].copy()
    if timestamps:
        ts = pd.to_datetime(prices['timestamp'])
        prices = prices[(ts >= min(timestamps)) & (ts <= max(timestamps))]
    return prices


def _assemble_portfolio_data(portfolio, timeframe, symbols, init_cash, benchmark_prices):
    return {
        'timeframe': timeframe,
        'symbols': symbols,
        'init_cash': init_cash,
        'benchmark_prices': benchmark_prices,
        'timestamps': portfolio.timestamps,
        'equity_curve': portfolio.equity_curve,
        'max_equity': portfolio.max_equity,
        'drawdowns': portfolio.drawdowns,
        'max_drawdown_amt': portfolio.max_drawdown_amt,
        'max_drawdown_pct': portfolio.max_drawdown_pct,
        'trade_history': portfolio.trade_history,
        'total_fees': portfolio.total_fees,
    }


def execute_backtest(strategy, candle_df, init_cash, slippage_bps, timeframe, symbols,
                     log_dir=None, start=None, end=None, fee_rate=0.0005):
    """Run one backtest over candle_df[start:end] and return its portfolio_data.

    Fresh components every call so repeated runs (folds, grid combos) never share
    state. log_dir=None routes logging to a NullLogger to avoid writing CSVs.
    """
    logger = Logger(base_path=log_dir) if log_dir else NullLogger()
    portfolio = Portfolio(logger, init_cash=init_cash)
    simulator = DummySimulator(slippage_bps=slippage_bps, fee_rate=fee_rate)
    executor = DummyExecutor(portfolio, simulator)
    backtester = Backtester(strategy, executor, simulator, portfolio, logger, candle_df)

    backtester.run_backtest(start=start, end=end)

    benchmark_prices = _benchmark_slice(candle_df, portfolio.timestamps)
    return _assemble_portfolio_data(portfolio, timeframe, symbols, init_cash, benchmark_prices)


def run_backtest(config):
    apply_defaults(config)
    strategy = config['strategy_class'](config['strategy_params'])
    candle_df = load_candle_data(config, strategy.required_features, strategy.required_multi_features)

    portfolio_data = execute_backtest(
        strategy, candle_df,
        init_cash=config['init_cash'],
        slippage_bps=config['slippage_bps'],
        timeframe=config['timeframe'],
        symbols=config['symbols'],
        log_dir=config['log_dir'],
        start=config.get('start'), end=config.get('end'),
        fee_rate=config.get('fee_rate', 0.0005),
    )

    save_path = f"{config['portfolio_save_dir']}/{config['name']}.pkl"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'wb') as f:
        pickle.dump(portfolio_data, f)
    return portfolio_data, save_path
