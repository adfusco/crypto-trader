# Test Suite Plan

Lock in the correctness fixes from Phase 1 and guard the bug-prone units against
regression. pytest, one file per unit.

## Setup
- [x] `pytest` dev dependency; `pytest.ini` with `testpaths=tests`, `pythonpath=.`.

## Coverage (one file per unit, targeting where bugs were found)
- [x] `test_circular_buffer.py` — append, wraparound order in `to_array`, `latest`, `__getitem__`.
- [x] `test_feature_functions.py` — `zscore` against hand-computed value (ddof=1).
- [x] `test_simulator.py` — slippage direction (long adds, short subtracts), fee formula.
- [x] `test_portfolio.py` — fresh open (cash/fee), `mark_to_market` equity/drawdown,
      full close PnL, **reversal fee proration** (`close_frac`), short-side PnL.
- [x] `test_engine.py` — lookahead: a bar-0 signal fills at bar-1 open (not bar 0);
      final bar flattens positions.
- [x] `test_walk_forward.py` — `generate_folds` count/boundaries, `param_combos`
      cartesian product, `stitch_equity` multiplicative chaining.

## Done after initial suite
- Fixed the partial same-side close bug in `Portfolio._update_position` (was misrouted
  to the add branch, realizing no PnL); added `test_partial_close_*` and `test_adding_*`.
