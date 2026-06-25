# Visualization Plan (Phase 3)

Deliver: equity vs. buy-and-hold, drawdown shading, trade markers.

## Step 0 — Augment PKL + re-run *(prerequisite)*
- [x] Add `init_cash`, `symbols`, `benchmark_prices` (timestamp + each `{symbol}_close`) to the save dict in `run.py`.
- [x] Re-run `main_backtest.py` and `main_backtest_multi.py` to regenerate both PKLs.

## Step 1 — `Metrics` data methods
- [x] Build `self.prices`, store `self.init_cash`, `self.symbols` in `__init__`.
- [x] `benchmark_curve()` → equal-weight buy-and-hold equity Series.
- [x] `underwater_series()` → negated `drawdown_pct`, timestamp-indexed.
- [x] `max_drawdown_window()` → `(peak_ts, trough_ts)` for shading.

## Step 2 — `metrics/plots.py`
- [x] `plot_performance(metrics)` → 2-panel shared-x Figure:
  - Top: strategy equity vs. benchmark; `axvspan` over max-drawdown window; trade markers at exits (green ▲ win / red ▼ loss).
  - Bottom: underwater fill_between(drawdown_pct, 0).
- Returns the Figure (no `plt.show()` inside).

## Step 3 — `metrics_engine.py` as thin driver
- [x] Strategy name via CLI arg; PKL path resolved relative to file.
- [x] Call `print_stats()`, then `plot_performance()` + `plt.show()`.

## Defaults locked in
- Benchmark = equal-weight basket.
- Trade markers on the equity line (symbol-count-agnostic).
