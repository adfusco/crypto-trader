import pandas as pd

from asset_analysis.make_df import get_top_syms
from asset_analysis.relationships import RELATIONSHIP_REGISTRY
from data_ingestion.fetch_ohlcv import csv_path, fetch_to_csvs

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


def load_price_df(symbols, price_col, path_to_csvs, timeframe='1d'):
    """Outer-join the given symbols' price_col series from their raw CSVs into a
    timestamp-indexed wide frame, columns ordered to match `symbols`.

    Outer join keeps each symbol's full history; callers align per use (a pair's
    overlapping range via dropna) so one short-history symbol doesn't truncate all.
    """
    df = None
    for symbol in symbols:
        path = csv_path(symbol, timeframe, path_to_csvs)
        series = pd.read_csv(path)[['timestamp', price_col]].rename(columns={price_col: symbol})
        df = series if df is None else df.merge(series, on='timestamp', how='outer')
    return df.sort_values('timestamp').set_index('timestamp')


def _slice_window(price_df, start, end):
    """Bound the price frame to [start, end]. The index is sorted ISO date strings,
    so lexicographic .loc slicing is chronological. Restricting the screen/estimate
    window is how you keep pair selection from peeking at out-of-sample data."""
    if start is None and end is None:
        return price_df
    return price_df.loc[start:end]


def screen_pairs(symbols, path_to_csvs, method='johansen', price_col='close',
                 timeframe='1d', start=None, end=None, **params):
    """Load `symbols` and rank their pairs by the named relationship method
    (see RELATIONSHIP_REGISTRY), screening only over [start, end]."""
    price_df = load_price_df(symbols, price_col, path_to_csvs, timeframe)
    price_df = _slice_window(price_df, start, end)
    return RELATIONSHIP_REGISTRY[method].require_screen()(price_df, **params)


def estimate_pair(symbols, price_col, path_to_csvs, method='johansen',
                  timeframe='1d', start=None, end=None, **params):
    """Estimate the tradeable parameter (e.g. hedge ratio) for one pair from CSVs
    over [start, end] -> (param, meta). See RELATIONSHIP_REGISTRY[method].estimate."""
    price_df = load_price_df(list(symbols), price_col, path_to_csvs, timeframe)
    price_df = _slice_window(price_df, start, end)
    return RELATIONSHIP_REGISTRY[method].require_estimate()(price_df, **params)


def main(num_symbols=30, by='quoteVolume', path_to_csvs='data_ingestion/raw_csvs',
         fetch=False, method='johansen', start='2019-01-01', timeframe='1d'):
    symbols = [symbol for symbol, _ in get_top_syms(num_symbols, by)]
    if fetch:
        fetch_to_csvs(symbols, timeframe, start, None, path_to_csvs)
    print(screen_pairs(symbols, path_to_csvs, method=method, timeframe=timeframe))


if __name__ == '__main__':
    main()
