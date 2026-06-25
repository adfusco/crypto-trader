import itertools

import pandas as pd

from backtest.run import apply_defaults, load_candle_data, execute_backtest, _benchmark_slice
from feature_engineering.rolling_features import add_rolling_features
from metrics.metrics import Metrics


def generate_folds(timestamps, train_size, test_size, step):
    """Rolling (train, test) boundaries as (tr_start, tr_end, te_start, te_end).

    timestamps: ordered sequence of bar timestamps. With step == test_size the
    test segments tile the timeline without gaps or overlaps.
    """
    timestamps = list(timestamps)
    n = len(timestamps)
    folds = []
    start = 0
    while start + train_size + test_size <= n:
        tr_start = timestamps[start]
        tr_end = timestamps[start + train_size - 1]
        te_start = timestamps[start + train_size]
        te_end = timestamps[start + train_size + test_size - 1]
        folds.append((tr_start, tr_end, te_start, te_end))
        start += step
    return folds


def param_combos(param_grid):
    """Cartesian product of a {param_name: [values]} grid -> list of param dicts."""
    keys = list(param_grid.keys())
    return [dict(zip(keys, values)) for values in itertools.product(*(param_grid[k] for k in keys))]


def sharpe_objective(metrics):
    """Default fit objective: in-sample Sharpe over the scored window."""
    return metrics.sharpe_ratio(metrics.timestamps[0], metrics.timestamps[-1], metrics.timeframe)


# name -> callable, so config files can reference an objective by string
OBJECTIVE_REGISTRY = {
    'sharpe': sharpe_objective,
}


def _equity_series(portfolio_data):
    eq = pd.DataFrame(portfolio_data['equity_curve'])
    if eq.empty:
        return pd.Series(dtype=float)
    eq['timestamp'] = pd.to_datetime(eq['timestamp'])
    eq = eq[~eq['timestamp'].duplicated(keep='first')]
    return eq.set_index('timestamp')['equity']


def fit_params(config, base_params, candle_df, train_start, train_end, symbols=None):
    """Grid-search the trading-rule params on the train slice; return the combo
    with the best objective score. `base_params` is the (possibly fold-local)
    starting point each grid combo is layered onto. `symbols` is the fold's traded
    set (the selected pair under walk-forward selection)."""
    objective = config.get('objective', sharpe_objective)
    symbols = symbols or config['symbols']

    best_score = None
    best_params = None
    for combo in param_combos(config['param_grid']):
        params = {**base_params, **combo}
        strategy = config['strategy_class'](params)
        portfolio_data = execute_backtest(
            strategy, candle_df,
            init_cash=config['init_cash'],
            slippage_bps=config['slippage_bps'],
            timeframe=config['timeframe'],
            symbols=symbols,
            start=train_start, end=train_end,
            fee_rate=config.get('fee_rate', 0.0005),
        )
        try:
            score = objective(Metrics(portfolio_data))
        except Exception:
            # degenerate window (no trades, zero volatility, etc.) -> unselectable
            score = float('-inf')

        if best_score is None or score > best_score:
            best_score = score
            best_params = params

    return best_params, best_score


def stitch_equity(fold_equities, init_cash):
    """Chain OOS test equity curves multiplicatively into one continuous curve
    that compounds from init_cash."""
    running = init_cash
    pieces = []
    for eq in fold_equities:
        if eq.empty:
            continue
        scaled = eq * (running / eq.iloc[0])
        pieces.append(scaled)
        running = scaled.iloc[-1]
    return pd.concat(pieces) if pieces else pd.Series(dtype=float)


def _drawdowns_from_equity(equity_series):
    """Re-derive the drawdown structures from a stitched equity curve, matching
    the shape Portfolio/Metrics expect."""
    max_eq = float('-inf')
    drawdowns = []
    max_dd_amt = {'amt': 0.0, 'pct': 0.0}
    max_dd_pct = {'pct': 0.0, 'amt': 0.0}

    for ts, eq in equity_series.items():
        max_eq = max(max_eq, eq)
        amt = max_eq - eq
        pct = amt / max_eq if max_eq else 0.0
        if amt > max_dd_amt['amt']:
            max_dd_amt = {'amt': amt, 'pct': pct}
        if pct > max_dd_pct['pct']:
            max_dd_pct = {'pct': pct, 'amt': amt}
        drawdowns.append({'timestamp': ts, 'drawdown_amt': amt,
                          'drawdown_pct': pct, 'equity': eq, 'peak': max_eq})

    return drawdowns, max_dd_amt, max_dd_pct, max_eq


def _assemble_oos_data(config, candle_df, stitched, trade_history, total_fees):
    """Build a Metrics-compatible portfolio_data dict from the stitched OOS curve."""
    equity_curve = [{'timestamp': ts, 'equity': eq} for ts, eq in stitched.items()]
    drawdowns, max_dd_amt, max_dd_pct, max_eq = _drawdowns_from_equity(stitched)

    return {
        'timeframe': config['timeframe'],
        'symbols': config['symbols'],
        'init_cash': config['init_cash'],
        'benchmark_prices': _benchmark_slice(candle_df, list(stitched.index)),
        'timestamps': list(stitched.index),
        'equity_curve': equity_curve,
        'max_equity': max_eq,
        'drawdowns': drawdowns,
        'max_drawdown_amt': max_dd_amt,
        'max_drawdown_pct': max_dd_pct,
        'trade_history': trade_history,
        'total_fees': total_fees,
    }


def walk_forward(config):
    """Run rolling walk-forward validation.

    Returns {'folds': [...per-fold records...], 'oos_data': portfolio_data} where
    oos_data is the stitched out-of-sample result (the credible, headline curve).
    """
    apply_defaults(config)
    proto = config['strategy_class'](config['base_params'])
    # Load prices for the whole configured universe with single-asset features
    # only; any multi-asset feature (e.g. the spread z-score) depends on the
    # fold's selected pair + fold-local params and is rebuilt per fold.
    raw_df = load_candle_data(config, proto.required_features, {}, symbols=config['symbols'])

    # bound the fold universe to the configured window
    ts_series = pd.to_datetime(raw_df['timestamp'])
    start, end = config.get('start'), config.get('end')
    if start is not None:
        raw_df = raw_df[ts_series.values >= pd.Timestamp(start)]
    if end is not None:
        raw_df = raw_df[pd.to_datetime(raw_df['timestamp']).values <= pd.Timestamp(end)]
    raw_df = raw_df.reset_index(drop=True)

    ts_series = pd.to_datetime(raw_df['timestamp'])
    timestamps = list(ts_series.drop_duplicates())
    folds = generate_folds(timestamps, config['train_size'], config['test_size'], config['step'])

    fold_records = []
    fold_equities = []
    oos_trades = []
    total_fees = 0.0

    for tr_start, tr_end, te_start, te_end in folds:
        train_prices = raw_df[(ts_series >= tr_start).values & (ts_series <= tr_end).values]

        # choose the fold's traded symbols from the universe on the train window
        # only (no test-window peek). None -> nothing tradeable; sit the fold out.
        selected = proto.select_universe(train_prices)
        if not selected:
            fold_equities.append(pd.Series(dtype=float))  # flat: no position held
            fold_records.append({
                'train_start': tr_start, 'train_end': tr_end,
                'test_start': te_start, 'test_end': te_end,
                'pair': None, 'params': None, 'train_score': None,
                'test_return': 0.0, 'num_trades': 0,
            })
            continue

        # fit fold-local params (e.g. hedge ratio) for the selected pair, train-only
        sel_params = {**config['base_params'], 'symbols': selected}
        overrides = config['strategy_class'](sel_params).fit_fold_params(train_prices)
        fold_params = {**sel_params, **overrides}

        # rebuild any multi-asset features for this fold's selected pair + params
        fold_strategy = config['strategy_class'](fold_params)
        if fold_strategy.required_multi_features:
            fold_df = add_rolling_features(raw_df, fold_strategy.required_multi_features)
        else:
            fold_df = raw_df

        best_params, train_score = fit_params(config, fold_params, fold_df, tr_start, tr_end, selected)

        strategy = config['strategy_class'](best_params)
        test_data = execute_backtest(
            strategy, fold_df,
            init_cash=config['init_cash'],
            slippage_bps=config['slippage_bps'],
            timeframe=config['timeframe'],
            symbols=selected,
            start=te_start, end=te_end,
            fee_rate=config.get('fee_rate', 0.0005),
        )

        test_metrics = Metrics(test_data)
        fold_equities.append(_equity_series(test_data))
        oos_trades.extend(test_data['trade_history'])
        total_fees += test_data['total_fees']

        fold_records.append({
            'train_start': tr_start,
            'train_end': tr_end,
            'test_start': te_start,
            'test_end': te_end,
            'pair': selected,
            **{k: round(v, 4) for k, v in overrides.items()},  # fold-local fits (e.g. beta)
            'params': {k: best_params[k] for k in config['param_grid']},
            'train_score': train_score,
            'test_return': test_metrics.total_return(te_start, te_end),
            'num_trades': len(test_data['trade_history']),
        })

    stitched = stitch_equity(fold_equities, config['init_cash'])
    oos_data = _assemble_oos_data(config, raw_df, stitched, oos_trades, total_fees)

    return {'folds': fold_records, 'oos_data': oos_data}
