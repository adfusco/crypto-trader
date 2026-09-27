# Crypto Trader

An event-driven backtesting engine for cryptocurrency strategies, with walk-forward validation, transaction costs, and slippage.

## Features

- Event driven engine with next-bar fills
- Walk-forward validation with fold-local fitting
- Cointegration screening
- Pairs mean-reversion strategy trading a hedged cointegration spread
- Fixed-fractional position sizing, slippage, and fee modeling
- Transaction-cost sensitivity sweep that finds the break-even slippage or fee level for a strategy
- Pluggable strategies, objectives, and relationship methods, selected by name from registries
- Equity-vs-benchmark, drawdown, and trade-marker visualization
- Config-driven CLI: commands to run a backtest or a full walk-forward with printed summary stats

## Architecture

```
ccxt OHLCV  =>  prepare + merge + features  =>  Backtester loop  =>  Metrics / plots
                                                      |
                                      Strategy.gen_signal => gen_order
                                                      |
                                   Executor => Simulator (slippage, fills)
                                                      |
                                   Portfolio (positions, P&L, equity curve)
```

The `Backtester` is what drives the bar by bar loop. The `Strategy` produces a signal from current state, the `Executor` and `Simulator` turn it into a filled order on the next bar, and the `Portfolio` tracks positions, realized and unrealized P&L, fees, and the equity curve that `Metrics` uses.

Directory Structure:

| Directory | Role |
|---|---|
| `data_ingestion/` | Async ccxt OHLCV fetching, CSV caching, merge and feature prep |
| `feature_engineering/` | Rolling single-asset and multi-asset (spread) features |
| `strategies/` | Strategy base class, registry, and mean-reversion strategies |
| `backtest/` | Event-driven engine, executor, simulator, portfolio, walk-forward |
| `asset_analysis/` | Cointegration / correlation screening and hedge-ratio estimation |
| `metrics/` | Performance metrics and plotting |
| `configs/` | One config per strategy mode combination |
| `tests/` | Unit tests for engine, portfolio, relationships, config |

## How to

```bash
pip install -r requirements.txt

# single backtest, with chart
python -m backtest mr_pairs_backtest --plot

# full walk-forward with per-fold pair selection
python -m backtest mr_pairs_select_walkforward
```

Data is read from cached CSVs by default. You can add `--fetch` to re-download from the exchange first.

## Example result

Below is the result from a walk-forward test over six symbols (DOT, XTZ, LINK, ADA, ATOM, LTC), where 2021-2025 is out-of-sample:

```bash
python -m backtest mr_pairs_select_walkforward
```

| Metric | Blind per-fold selection | Fixed DOT/XTZ (chosen in-sample) |
|---|---|---|
| OOS total return | +5.85% | +10.23% |
| CAGR | 1.45% | - |
| Max drawdown | 6.52% | 4.62% |
| Profit factor | 1.23 | 1.29 |
| Trades | 86 | 106 |

Notice that the selector trades a different pair on most folds, and sits out 2 of 17 when nothing cointegrates. The gap between the two columns is the selection bias an in-sample pair choice would have hidden.

![Walk-forward equity vs buy-and-hold](docs/images/walkforward_equity.png)

The strategy (blue) stays roughly flat and market-neutral while the buy-and-hold basket (gray) falls from 120k to 30k through the 2022 bear market.

## Configuration

A config is a plain dict in `configs/<name>.py`, named `<strategy>_<mode>` (for example `mr_pairs_select_walkforward`). The CLI loads it by name and dispatches on its `mode` key:

```python
config = {
    'mode': 'backtest',          # or 'walkforward'
    'strategy': 'mr_pairs',      # registry name
    'symbols': ['DOT/USDT', 'XTZ/USDT'],
    'timeframe': '1d',
    'start': '2022-01-01',       # bounds both fetch range and backtest slice
    'end': None,                 # None = up to latest
    'init_cash': 100000.0,
    'slippage_bps': 5,
    'strategy_params': { ... },  # or base_params + param_grid for walkforward
}
```

## Strategies and relationships

Here are some sample strategies included:

| Strategy | Description |
|---|---|
| `mr_basic` | Single-asset z-score mean reversion |
| `mr_multi` | Independent per-symbol mean reversion across a basket |
| `mr_pairs` | Mean reversion on a hedged cointegration spread, beta from the relationship method |

| Relationship | Provides |
|---|---|
| `johansen` | Screening (cointegration trace) and hedge-ratio estimation |
| `correlation` | Screening only (return correlation) |
| `ols` | Hedge-ratio estimation only (regression) |

## Screening workflow

Rank the candidate pairs in a universe before adding one to a config:

```bash
python -m asset_analysis DOT/USDT XTZ/USDT LINK/USDT ADA/USDT --start 2020-09-01 --top 10
```

This prints every testable pair ranked by trace statistic, with a `cointegrated` flag and the estimated hedge ratio. Add `--fetch` to pull data first, `--method correlation` to switch the screen, or `--save out.csv` to write the full table.

## Transaction cost sensitivity

Rerun any config across a range of slippage or fee levels to see how far the edge lasts against rising transaction costs:

```bash
python -m backtest.cost_sweep mr_pairs_backtest --param slippage_bps --plot
```

![Total return vs slippage](docs/images/cost_sweep.png)

For `mr_pairs_backtest` the return crosses zero around 44 bps of slippage, so the edge is relatively thin and cost-sensitive. Swap `--param fee_rate` to sweep fees, or `--metric sharpe_ratio` to plot a different axis. The sweep reuses the main CLI's run path, so it works for any strategy or mode unchanged.

## Testing

```bash
pytest -q
```

Included are 40 tests covering engine fill logic, portfolio P&L and partial closes, relationship estimators and screeners, pair selection, and config validation.

## Limitations

- Live and paper trading are not implemented
- A single train window controls both pair selection and beta fitting (there is no separate cointegration lookback)
- Primarily tested on daily data
- Fees and slippage use a simple constant model

## Installation

```bash
git clone https://github.com/adfusco/crypto-trader
cd crypto-trader
pip install -r requirements.txt
```
