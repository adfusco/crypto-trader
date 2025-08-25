import pandas as pd
import feature_engineering.rolling_feature_functions as rffs


def fn_wrapper(fn):
    def wrapper(df, **params):
        return fn(df, **params)
    return wrapper

ROLLING_FEATURE_FUNCTIONS = {
    'zscore':fn_wrapper(rffs.zscore),
    'pairs_spread':fn_wrapper(rffs.pairs_spread),
}


def add_rolling_features(df, required_features=None):
    df = df.copy()

    if not required_features is None:
        for feature, param_dict in required_features.items():
            if feature in ROLLING_FEATURE_FUNCTIONS:
                col_dict = ROLLING_FEATURE_FUNCTIONS[feature](df, **param_dict)
                for col, series in col_dict.items():
                    df[col] = series
            else:
                raise ValueError('unknown feature')

    df = df.dropna()
    return df