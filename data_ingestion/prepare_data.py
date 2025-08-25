import pandas as pd
import os

from data_ingestion.fetch_ohlcv import get_path_symbol
from feature_engineering.rolling_features import add_rolling_features

def match_sort_paths(symbols, path_to_csvs):
    paths = set(os.path.join(path_to_csvs, path) for path in os.listdir(path_to_csvs))

    syms_and_paths = {}
    for symbol in symbols:
        csv_name = f'{get_path_symbol(symbol)}.csv'
        full_path = os.path.join(path_to_csvs, csv_name)
        if full_path in paths:
            syms_and_paths[symbol] = full_path

    syms_and_paths = dict(sorted(syms_and_paths.items()))
    symbols = list(syms_and_paths.keys())
    paths = list(syms_and_paths.values())

    return symbols, paths

def load_prepare_df(path, symbol, use_precomputed_features, single_asset_features, merge_on):
    df = pd.read_csv(path)
    if use_precomputed_features and single_asset_features:
        df = add_rolling_features(df, single_asset_features)
    return df.rename(columns=lambda x: f'{symbol}_' + x if x != merge_on else x)

def prepare_candle_data(symbols, use_precomputed_features, single_asset_features, multi_asset_features, path_to_csvs, path_to_output_csv, merge_on='timestamp'):
    symbols, paths = match_sort_paths(symbols, path_to_csvs)

    output_df = load_prepare_df(paths[0], symbols[0], use_precomputed_features, single_asset_features, merge_on)
    for i, path in enumerate(paths[1:], start=1):
        right = load_prepare_df(path, symbols[i], use_precomputed_features, single_asset_features, merge_on)

        overlapping = output_df.columns.intersection(right.columns)
        overlapping = overlapping.difference([merge_on])
        right_filtered = right.drop(columns=overlapping)

        output_df = pd.merge(left=output_df, right=right_filtered, on=merge_on, how='left')

    if use_precomputed_features and multi_asset_features:
        output_df = add_rolling_features(output_df, multi_asset_features)

    output_df.to_csv(path_to_output_csv)
    return output_df