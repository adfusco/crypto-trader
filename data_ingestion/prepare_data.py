import pandas as pd
import os
from datetime import datetime

from data_ingestion.fetch_ohlcv import get_path_symbol
from feature_engineering.rolling_features import add_rolling_features

def prepare_candle_data(symbols, use_precomputed_features, features, path_to_csvs='data', path_to_output='data', merge_on='timestamp'):
    path_symbols = [get_path_symbol(symbol) for symbol in symbols]
    paths = list(os.path.join(path_to_csvs, path) for path in os.listdir(path_to_csvs) if path.strip('.csv') in path_symbols)
    paths, symbols = zip(*sorted(zip(paths, symbols)))

    output_df = pd.read_csv(paths[0])
    if use_precomputed_features: output_df = add_rolling_features(output_df, features)
    output_df = output_df.rename(columns=lambda x: f'{symbols[0]}_' + x if x != 'timestamp' else x)

    for path in paths[1:]:
        right = pd.read_csv(path)
        if use_precomputed_features: right = add_rolling_features(right, features)
        right = right.rename(columns=lambda x: f'{symbols[0]}_' + x if x != 'timestamp' else x)

        overlapping = output_df.columns.intersection(right.columns)
        overlapping = overlapping.difference([merge_on])
        right_filtered = right.drop(columns=overlapping)

        output_df = pd.merge(output_df, right_filtered, on=merge_on)

    #output_df.to_csv(path_to_output + '/' + str(datetime.now()) + '.csv') unique file version
    output_df.to_csv(path_to_output + '/' + 'current_data' + '.csv')
    return output_df