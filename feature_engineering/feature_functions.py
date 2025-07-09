import pandas as pd
import numpy as np

def zscore(window_arr):
    s = pd.Series(window_arr)
    mean = s.mean()
    std = s.std()

    return (s.iloc[-1] - mean)/std