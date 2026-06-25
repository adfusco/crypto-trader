import numpy as np

import feature_engineering.feature_functions as ffs


def test_zscore_matches_hand_computation():
    arr = np.array([1, 2, 3, 4, 5])
    # mean=3, sample std (ddof=1)=sqrt(2.5)=1.58114, z=(5-3)/1.58114
    expected = (5 - 3) / np.sqrt(2.5)
    assert ffs.zscore(arr) == np.float64(expected) or abs(ffs.zscore(arr) - expected) < 1e-9


def test_zscore_zero_at_mean():
    # last value equal to the mean -> z == 0
    arr = np.array([2, 4, 3])  # mean=3, last=3
    assert abs(ffs.zscore(arr) - 0.0) < 1e-9
