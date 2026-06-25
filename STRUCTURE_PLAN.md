# Structure Plan — Entry Points & asset_analysis

Two edge-of-repo cleanups. Options laid out; pick one path each.

## A. Entry-point sprawl
Five root scripts (`main_backtest`, `main_backtest_multi`, `main_pairs`,
`main_walkforward`, `main_live`) are each ~30 lines of config + one call. `main_live`
is empty.

### Option A1 — Move configs to a folder, keep thin scripts (low effort)
- `experiments/` holds the current scripts unchanged; root stays clean.
- Pro: trivial, low risk. Con: still N near-duplicate scripts.

### Option A2 — Config files + one CLI (recommended, medium effort)
- `configs/*.py` (or `.yaml`) hold pure config dicts; one `python -m backtest.run <config>`
  dispatches to `run_backtest` / `walk_forward` by a `mode` key.
- Pro: kills duplication, one entry point, configs are data. Con: needs a small CLI
  loader + (if yaml) a parser; strategy_class/objective must resolve from a registry
  rather than direct import.

### Option A3 — Single CLI with argparse subcommands (medium/high effort)
- `python -m backtest run|walkforward|pairs --strategy ... --symbols ...`
- Pro: most "tool-like". Con: most code; over-engineered for a few experiments.

- [x] Decided **A2** (config files + one CLI).
- [x] Implemented: `configs/*.py` + `python -m backtest <config>` dispatching by `mode`.
- [x] `main_live.py` deleted (was empty); all `main_*.py` removed.
- [x] Strategy registry (`strategies/registry.py`) + objective registry (`walk_forward.OBJECTIVE_REGISTRY`).

## B. asset_analysis cleanup
`make_df.py` and `analysis_engine.main()` use hardcoded relative paths
(`'../data_ingestion/raw_csvs'`), a `saved` boolean toggle, and only run from their
own directory — out of step with the config-driven rest. (`johansen_hedge_ratio` /
`load_price_df` were cleaned up already.)

- [x] Removed relative paths; `screen_pairs` / `johansen_hedge_ratio` take `path_to_csvs`.
- [x] Replaced the `saved` toggle with a `fetch` flag on `main()`.
- [x] Moved the fetch wrapper to `data_ingestion.fetch_to_csvs` (shared by `run.py` and
      `analysis_engine`); removed redundant `make_df.get_merged_df`.
- [x] Screening `main()` is now `screen_pairs(symbols, path_to_csvs, ...)` returning the
      cointegrated-pairs table; thin `__main__` wrapper. Also fixed an empty-result crash.
- [~] Folding `make_df` into `data_ingestion`: deferred — `get_top_syms` (volume ranking)
      is an analysis concern, kept in `asset_analysis`.

## Decisions to lock in
- A2 recommended for entry points (configs as data + registry).
- asset_analysis should consume the same `fetch`/path config keys as `run.py` for consistency.
