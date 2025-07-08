import pandas as pd
import numpy as np

def compute_newest_zscore(window, series):
    if len(series) < window:
        pass

    s = pd.Series(series[-window:])
    mean = s.mean()
    std = s.std()

    return (s.iloc[-1] - mean)/std