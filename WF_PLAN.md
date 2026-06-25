# Walk-Forward Validation Plan (Phase 3)

Rolling train/test windows: fit params on train, evaluate on held-out test, stitch
out-of-sample (OOS) segments into one credible equity curve.

## Key decision
Features are **precomputed once on the full causal series** (`use_precomputed_features=True`),
so the grid tunes the **trading rule** (z-thresholds, `risk_pct`), not the feature `window`.
Avoids a per-fold warmup gap; searching `window` later means precomputing multiple windows.

## Step 0 — Reusable single-run core (`run.py` refactor)
- [x] `fetch_data(...)` — async OHLCV fetch, split out of `run_backtest`.
- [x] `load_candle_data(config, required_features)` — optional fetch (via `config['fetch']`) + prepare.
- [x] `execute_backtest(strategy, candle_df, init_cash, slippage_bps, timeframe, symbols, log_dir=None, start=None, end=None)` → `portfolio_data` dict. Fresh components each call; `log_dir=None` → `NullLogger`.
- [x] `run_backtest(config)` reduced to: load data → `execute_backtest` → save PKL.

## Step 1 — `NullLogger` (`logger.py`)
- [x] No-op `log_trade` / `log_portfolio_update` / `flush_all` so fold/grid runs don't spam CSVs.

## Step 2 — Walk-forward module (`backtest/candle_backtester/walk_forward.py`)
- [x] `generate_folds(timestamps, train_size, test_size, step)` → `(tr_start, tr_end, te_start, te_end)` list; rolling, non-overlapping test segments (`step = test_size`).
- [x] `param_combos(param_grid)` → cartesian product of grid.
- [x] `fit_params(...)` — grid search on the train slice; score via objective; return best params.
- [x] `sharpe_objective(metrics)` — default objective (configurable callable).
- [x] `stitch_equity(fold_equities, init_cash)` — chain OOS test curves multiplicatively.
- [x] `walk_forward(config)` — per fold: fit on train → run test → record; stitch; assemble OOS `portfolio_data` (re-derive drawdowns, concat trades); return folds table + OOS data.

## Step 3 — Entry point (`main_walkforward.py`)
- [x] Thin config: strategy_class, base_params, param_grid, objective, window sizes, data keys.

## Supporting fixes
- [x] `Metrics.__init__` tolerates empty `trade_history` (degenerate grid combos).

## Defaults to lock in
- Rolling windows; objective = train Sharpe; small grid (overfitting risk on ~960 daily bars).
- Suggested: train 365 / test 90 / step 90 → ~6 folds. Limited — state it honestly in results.
