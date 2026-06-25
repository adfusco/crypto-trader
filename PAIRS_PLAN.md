# True Pairs Strategy Plan (Phase 3)

Trade one cointegrated spread (`price_A − β·price_B`); the spread's z-score drives
a single hedged decision. Single-pair first.

## Step 1 — Rename the misnomer
- [x] `mr_cross.py` → `mr_multi.py`; class `MeanReversionPair` → `MeanReversionMulti`
      (it's independent per-symbol MR). Update imports in `main_backtest_multi.py`,
      `main_walkforward.py`.

## Step 2 — Spread z-score feature (`rolling_features.py`)
- [x] `spread_zscore(df, hedge_ratio, symbols, price_col, window)` → rolling z of
      `price_A − β·price_B`; register in `ROLLING_FEATURE_FUNCTIONS`. Multi-asset (post-merge).

## Step 3 — Route multi-asset features (`base.py`, `run.py`)
- [x] Base `Strategy.__init__` defaults `required_features = {}`, `required_multi_features = {}`.
- [x] `load_candle_data(config, strategy)` passes both single (`required_features`) and
      multi (`required_multi_features`) into `prepare_candle_data`. Update callers in
      `run.py` and `walk_forward.py`. Existing strategies unaffected (empty multi dict).

## Step 4 — `mr_pairs.py` → `PairsMeanReversion`
- [x] params: `symbols` (2), `hedge_ratio`, `window`, `price_col`, `zscores` (on spread z),
      `risk_pct`, `use_precomputed_features`.
- [x] `required_multi_features = {'spread_zscore': {...}}`.
- [x] state: one spread position — `None` / `long_spread` / `short_spread` (from leg-A side).
- [x] `gen_signal`: single decision — long spread when `z < long_entry`, short when
      `z > short_entry`, exit toward `z ≈ 0`.
- [x] `gen_order`: spread signal → two hedged leg orders in one dict.
      long spread = long A + short B; short spread = short A + long B.
      Sizing: `qty_A = int(equity·risk_pct / price_A)`, `qty_B = int(qty_A·β)`.
      Exit = close both legs at held quantities (flat).

## Step 5 — Wire up + smoke test
- [x] `main_pairs.py` (config-only). `hedge_ratio` sourced manually from `analysis_engine`
      (normalize cointegrating vector so leg-A = 1); placeholder β for now.
- [x] Run one `run_backtest` to verify wiring end-to-end.

## Decisions locked in
- β-proportional leg sizing (not dollar-neutral).
- Exit → flat (not flip).
- "long spread" = long A, short B.
- Precomputed features; β + window fixed per run, tune z-thresholds.
