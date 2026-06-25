import pandas as pd

from backtest.walk_forward import (
    generate_folds, param_combos, stitch_equity,
)


def test_generate_folds_count_and_boundaries():
    ts = list(range(100))
    folds = generate_folds(ts, train_size=40, test_size=20, step=20)
    assert len(folds) == 3  # starts at 0, 20, 40

    tr_start, tr_end, te_start, te_end = folds[0]
    assert (tr_start, tr_end, te_start, te_end) == (0, 39, 40, 59)

    # non-overlapping, contiguous test segments when step == test_size
    assert folds[1][2] == 60  # second test starts where first ended + 1
    assert folds[2][3] == 99


def test_generate_folds_empty_when_too_short():
    assert generate_folds(list(range(50)), train_size=40, test_size=20, step=20) == []


def test_param_combos_cartesian_product():
    combos = param_combos({'a': [1, 2], 'b': [3, 4]})
    assert len(combos) == 4
    assert {'a': 1, 'b': 3} in combos
    assert {'a': 2, 'b': 4} in combos


def test_stitch_equity_chains_returns_multiplicatively():
    idx1 = pd.to_datetime(['2022-01-01', '2022-01-02'])
    idx2 = pd.to_datetime(['2022-01-03', '2022-01-04'])
    fold1 = pd.Series([100.0, 110.0], index=idx1)  # +10%
    fold2 = pd.Series([200.0, 220.0], index=idx2)  # +10%

    stitched = stitch_equity([fold1, fold2], init_cash=100.0)
    assert stitched.iloc[0] == 100.0
    # fold1 ends at 110; fold2 (+10%) compounds to 121
    assert abs(stitched.iloc[-1] - 121.0) < 1e-9
    assert len(stitched) == 4


def test_stitch_equity_empty_input():
    assert stitch_equity([], init_cash=100.0).empty
