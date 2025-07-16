import pandas as pd
import feature_engineering.rolling_feature_functions as rffs

ROLLING_FEATURE_FUNCTIONS = {
    'zscore':lambda df, **params: rffs.zscore_rolling(df, **params)
}

def add_rolling_features(df, required_features=None):
    df = df.copy()

    if not required_features is None:
        for feature, param_dict in required_features.items():
            if feature in ROLLING_FEATURE_FUNCTIONS:
                df[feature] = ROLLING_FEATURE_FUNCTIONS[feature](df, **param_dict)
            else:
                raise ValueError('unknown feature')

    df = df.dropna()
    return df