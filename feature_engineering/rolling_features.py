import pandas as pd
import feature_engineering.rolling_feature_functions as rffs

ROLLING_FEATURE_FUNCTIONS = {
    'zscore':lambda df, price_col, window: rffs.zscore_rolling(df, price_col, window)
}

def add_rolling_features(df, required_features=None):
    df = df.copy()

    if not required_features is None:
        for feature in required_features:
            if feature in ROLLING_FEATURE_FUNCTIONS:
                df[feature] = ROLLING_FEATURE_FUNCTIONS[feature](**required_features)
            else:
                raise ValueError('unknown feature')

    df = df.dropna()
    return df