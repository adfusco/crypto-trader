# Crypto Trader — Completion Plan

## Phase 1: Bug Fixes
*Correctness before anything else — existing backtest results are wrong.*

- [x] **Lookahead bias** (`candle_engine.py`) — fills execute on the current bar's close; signals should fill on the *next* bar's open. Fix: pending-orders queue, execute on bar `i+1`.
- [x] **`_close_positions` qty** (`candle_engine.py`) — hardcodes `qty=1/-1` instead of reading `abs(pos['qty'])` from the portfolio. Final-bar P&L is wrong for any non-unit position.
- [x] **Simulator side mapping** (`candle_simulator.py`) — slippage direction checks `'buy'/'sell'` but strategies emit `'long'/'short'`. Slippage is always applied in the wrong direction.
- [x] **Simulator exec price** (`candle_simulator.py`) — hardcodes `'close'`; with the pending-orders fix, fills should use the *next* bar's `'open'`.
- [x] **`CircularBuffer.to_array()`** (`circular_buffer.py`) — `np.concatenate(a, b)` should be `np.concatenate([a, b])`. Crashes silently in the non-precomputed path.
- [x] **`CircularBuffer.latest()`** (`circular_buffer.py`) — `% self.size` applied to the *value* instead of the index.
- [x] **`MeanReversionPair.gen_signal()`** (`mr_cross.py`) — references `self.state['symbols']` (never set); should be `self.params['symbols']`. Strategy is unrunnable.
- [x] **`MeanReversionPair.gen_signal()` hold case** (`mr_cross.py`) — raises `ValueError` when holding instead of returning `{'side': 'hold'}`.
- [x] **`MeanReversionPair.gen_order()`** (`mr_cross.py`) — treats `signal` as a flat dict, but `gen_signal` returns a dict keyed by symbol.
- [x] **Zscore key inconsistency** — `default_params` used `entry_long`/`exit_long` style while `gen_signal` reads `long_entry`/`long_exit`; `main_backtest_multi.py` had a mixed set. Standardised to `long_entry`/`long_exit`/`short_entry`/`short_exit` everywhere.
- [x] **Closing fee math** (`candle_portfolio.py`) — partial-close proration `(old_qty / abs(signed_qty)) * fee` multiplies a dimensionless ratio by a dollar amount. P&L is silently wrong on any position close.
- [x] **Fetch pagination duplicate** (`fetch_ohlcv.py`) — `fetch_ohlcv(since=X)` is inclusive, but each batch's next `since` was set to the last candle already fetched, re-fetching it as a duplicate at every 500-row boundary. Duplicate bars got double-processed (extra mark-to-market + signal eval) and produced duplicate timestamps in the equity curve. Fix: advance `since` by one timeframe (`step_ms`) past the last candle. Existing raw CSVs de-duplicated and PKLs regenerated.
- [x] **Rerun both backtests** — existing PKLs (`MeanReversionBasic.pkl`, `MeanReversionPair.pkl`) were generated before Phase 1 fixes. All current results are invalid and must be regenerated before any analysis.

---

## Phase 2: Core Completeness
*Makes the project actually do what it claims.*

- [x] **Position sizing** — replaced `qty = 1` with fixed-fractional sizing (2% of equity per trade). `risk_pct` is a configurable strategy param.
- [x] **Multi-asset backtest end-to-end** (`main_backtest_multi.py`) — `MeanReversionPair` now runs across ETH/USDT + SOL/USDT with the same portfolio/executor/simulator stack.
- [x] **Logger flush on exit** (`candle_logger.py`) — `flush_trade_log` / `flush_portfolio_log` only trigger when the buffer hits `flush_point` (100). If a backtest ends with fewer pending entries, the last batch is never written to CSV. Add a `flush_all()` call at the end of `Backtester.run_backtest()`.
- [x] **`if __name__ == '__main__':` guards** (`main_backtest.py`, `main_backtest_multi.py`) — top-level code runs on import, making both files untestable and fragile. Wrap in guards.
- [x] **Config-driven entry point** — both main scripts share ~80% identical boilerplate. Replace with a single `run_backtest(config)` function that accepts a config dict; each strategy gets a config file instead of a copy-pasted script.
- [x] **Feature engineering consolidation** — concern is split across three files with inconsistent naming: `feature_functions.py` (stateless, CircularBuffer path), `rolling_feature_functions.py` (DataFrame rolling), `rolling_features.py` (dispatcher). Collapse into one or two files with clear names.
- [x] **`__init__.py` files** — modules rely on implicit namespace packages. Add `__init__.py` to each package directory for explicit, conventional imports.

---

## Phase 3: Worth Talking About
*Ordered by impact.*

- [x] **Visualization** — equity curve vs. buy-and-hold benchmark, drawdown shading, trade entry/exit markers. Do this first: makes every subsequent result self-explanatory and is the fastest demonstrable win.
- [x] **Walk-forward validation** — rolling train/test windows; fit on train, evaluate on held-out test (`walk_forward.py`). Includes fold-local hedge-ratio re-fitting (`fit_fold_params`) so beta never sees test data. Validated on DOT/XTZ: +10.2% OOS, 4.6% max DD, PF 1.29 across 17 folds (2021–2025).
- [x] **Walk-forward pair selection** — closes the *selection*-bias leak that fold-local beta doesn't: today the traded pair is hand-picked from full-sample cointegration, so the OOS curve is conditioned on a pair we already know survived. Add a `Strategy.select_universe(train_prices)` hook (default: trade the configured symbols) that the walk-forward loop calls per fold; `PairsMeanReversion` overrides it to screen the configured *universe* on that fold's train window only and trade the top cointegrated pair (or sit the fold out if none cointegrate). The pair, hedge ratio, and trading-rule params are then all fit train-only — no part of the decision touches the test window. Modular: gated by universe size (≤2 symbols → fixed pair, unchanged behavior), selection method pluggable via the relationship registry, non-pairs strategies inherit the no-op default. New config `mr_pairs_select_walkforward` (6-symbol universe) demonstrates it alongside the fixed-pair config.
- [x] **Transaction cost sensitivity** — `backtest/cost_sweep.py` (`sweep_costs`) re-runs any config across a grid of `slippage_bps` or `fee_rate` values and collects per-value metrics; `plot_cost_sweep` charts the metric vs cost and marks the break-even crossing. Threaded `fee_rate` through as a first-class config key. CLI: `python -m backtest.cost_sweep <config> --param slippage_bps --plot`. mr_pairs_backtest breaks even around 44 bps slippage.
- [x] **True pairs strategy** — renamed `mr_cross.py` → `mr_multi.py` (`MeanReversionMulti`, independent per-symbol MR); built `mr_pairs.py` (`PairsMeanReversion`) trading the cointegration spread with hedged legs. Added `spread_zscore` multi-asset feature and `required_multi_features` routing so post-merge features compute. Hedge ratio is a config param (manual OLS estimate for now; should come from `analysis_engine.py`'s Johansen vector).

---

## Phase 3.5: Usability
*Make a run self-contained, safe, and offline by default.*

- [x] **Print results after a run** — a backtest currently prints only a progress bar; you must run a second command to see anything. Print summary stats (return, Sharpe, max DD, trades) at the end of every run, plus a `--plot` flag to show the chart. One command → answers.
- [x] **Derive output paths from the config name** — output pkl is named by strategy class, so two configs using the same strategy silently overwrite each other's results; `path_to_merged_data`/`log_dir` must be hand-picked unique per config. Derive the pkl, merged-data path, and log dir from the (unique) config name; drop those plumbing keys from configs. Fixes silent clobbering and makes `metrics_engine <config_name>` predictable.
- [x] **Fetch off by default** — `mr_basic`/`mr_multi` configs re-download from the exchange on every run (`fetch: True`). Default `fetch: False` (reuse cached CSVs); add a `--fetch` CLI flag to opt in. Fetching becomes an explicit, occasional act.
- [x] **Date-based windows (`start`/`end`)** — replaced epoch-ms `since_ms`/`limit` with human `start`/`end` date strings bounding both the fetch range and the backtest slice (threaded into `execute_backtest` and the walk-forward fold universe). `end: None` = up to latest.
- [x] **Timeframe-tagged data + fail-loudly** — raw CSVs are now `{symbol}_{timeframe}.csv` (e.g. `ETH_USDT_1d.csv`) so one timeframe can't silently overwrite or be read as another. Missing cached data raises a clear `run with --fetch` error instead of silently dropping the symbol or using wrong-timeframe bars.

---

## Phase 4: Polish
*Resume-level presentation.*

- [x] **README with one real result** — table of strategy performance (Sharpe, CAGR, max drawdown) on a specific period vs. buy-and-hold. Concrete numbers are memorable. (Current README documents the deleted `main_backtest.py` flow — rewrite against the CLI.)

---

## Phase 5: Post-review Bug Fixes
*Found in a design review of the refactored code (2026-06-25). All 40 tests pass after.*

- [x] **`Portfolio.reset()` wrong args** (`portfolio.py`) — called `self.__init__(self.init_capital)`, passing cash into the `logger` positional. Dead code (no callers; runs build a fresh `Portfolio`), so removed entirely in the Phase 6 cleanup rather than left as a latent trap.
- [x] **`unrealized_pnl` mislabeled as market value** (`portfolio.py`) — `mark_to_market` accumulated `live_price * qty` (gross market value) under the name `unrealized_pnl`, so the value logged to the portfolio CSV / returned by `get_stats()` was not P&L. Equity was still correct (cash already holds cost basis). Fixed: `unrealized_pnl` now sums `(live_price - entry_price) * qty`; equity adds back a separate signed `total_market_value`.
- [x] **Leverage divide-by-zero** (`portfolio.py`) — `leverage_used = total_pos_value / self.equity` and `position_exposure` blew up when equity hit 0 (fully drawn-down / squeezed account). Guarded both to fall back to `0.0` when `equity` is falsy.

---

## Phase 6: Neatness & Consistency
*Codebase-wide tidy after the review surfaced a two-era split between polished and older modules. All 40 tests pass after.*

- [x] **Finished the half-done `candle_` rename** — flattened `backtest/candle_backtester/` up into `backtest/` (matches the README directory map) and renamed `metrics/candle_metrics.py` → `metrics/metrics.py`. Rewrote all imports (`backtest.candle_backtester.X` → `backtest.X`, `metrics.candle_metrics` → `metrics.metrics`) across source and tests.
- [x] **Removed dead methods** — `required_params()` (defined on `Strategy` + all three strategies, never called; validation runs on config keys) and `reset()` (on `Portfolio` + every strategy, no callers since each run builds fresh instances).
- [x] **Style/formatting pass** (no formatter installed, done by hand on the old-era files) — PEP8 dict spacing in `portfolio.py`/`simulator.py`, removed one-liner `if` bodies and trailing whitespace in `mr_basic.py`, fixed import grouping in `fetch_ohlcv.py`/`analysis_engine.py`, fixed the stale `Strategy.update_state` base signature to match subclasses.
- [x] **Stripped scratch comments** — the shout-TODO in `fetch_ohlcv.py`, the repeated `#add warnings/error raise?` notes in `logger.py`, and rewrote the misleading "dummy executor" / "dummy simulator" header comments to describe what they actually do.

---

## Backlog
*Worth doing eventually, not the highest-ROI next step.*

- **Paper trading (`main_live.py`)** — replay live websocket candles through the same stack without real orders. Architecturally interesting but low priority vs. walk-forward for a project presentation.
