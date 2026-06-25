import pandas as pd


def zscore(df, price_col, window=20):
    price_series = df[price_col]
    mean = price_series.rolling(window).mean()
    std = price_series.rolling(window).std()
    return {'zscore': (price_series - mean) / std}


def pairs_spread(df, hedge_ratio, symbols, price_col):
    sym_a, sym_b = symbols
    price_series_a = df[f'{sym_a}_{price_col}']
    price_series_b = df[f'{sym_b}_{price_col}']
    return {f'{sym_a}_{sym_b} pairs spread': price_series_a - hedge_ratio * price_series_b}


def spread_zscore(df, hedge_ratio, symbols, price_col, window=20):
    # rolling z-score of the cointegration spread price_A - beta * price_B
    sym_a, sym_b = symbols
    spread = df[f'{sym_a}_{price_col}'] - hedge_ratio * df[f'{sym_b}_{price_col}']
    mean = spread.rolling(window).mean()
    std = spread.rolling(window).std()
    return {'spread_zscore': (spread - mean) / std}


ROLLING_FEATURE_FUNCTIONS = {
    'zscore': zscore,
    'pairs_spread': pairs_spread,
    'spread_zscore': spread_zscore,
}


def add_rolling_features(df, required_features=None):
    df = df.copy()

    if required_features is not None:
        for feature, param_dict in required_features.items():
            if feature in ROLLING_FEATURE_FUNCTIONS:
                col_dict = ROLLING_FEATURE_FUNCTIONS[feature](df, **param_dict)
                for col, series in col_dict.items():
                    df[col] = series
            else:
                raise ValueError(f'unknown feature: {feature}')

    df = df.dropna()
    return df
