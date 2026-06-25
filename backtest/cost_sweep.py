"""Transaction-cost sensitivity: python -m backtest.cost_sweep <config> --param ...

Re-runs a config across a range of values for one cost parameter (slippage or
fee) and reports how the result degrades, so you can see the break-even cost
level. Reuses the same run paths as `python -m backtest`, so any strategy/mode
works unchanged.
"""
import argparse

import pandas as pd

from metrics.metrics import Metrics


def _portfolio_data(config):
    """Run `config` once and return its portfolio_data, WITHOUT run_backtest's pkl
    save (a sweep re-runs many times and would otherwise clobber the canonical
    result). Dispatches on mode like the main CLI."""
    from backtest.run import apply_defaults, load_candle_data, execute_backtest
    from backtest.walk_forward import walk_forward

    if config['mode'] == 'walkforward':
        return walk_forward(config)['oos_data']

    apply_defaults(config)
    strategy = config['strategy_class'](config['strategy_params'])
    candle_df = load_candle_data(config, strategy.required_features, strategy.required_multi_features)
    return execute_backtest(
        strategy, candle_df,
        init_cash=config['init_cash'], slippage_bps=config['slippage_bps'],
        timeframe=config['timeframe'], symbols=config['symbols'],
        start=config.get('start'), end=config.get('end'),
        fee_rate=config.get('fee_rate', 0.0005),
    )


def sweep_costs(config, param='slippage_bps', values=(0, 2.5, 5, 10, 20, 40, 80)):
    """Re-run a config across `values` for one cost `param` ('slippage_bps' or
    'fee_rate') and collect summary metrics per value. Returns a DataFrame with the
    cost axis as the first column. Only the swept key is overridden each run, so
    the strategy, data, and all other params are held fixed."""
    rows = []
    for value in values:
        trial = {**config, param: value}  # shallow: override only the cost knob
        metrics = Metrics(_portfolio_data(trial))
        stats = metrics.compute_stats()
        rows.append({
            param: value,
            'total_return': stats['total_return'],
            'sharpe_ratio': stats['sharpe_ratio'],
            'profit_factor': stats['profit_factor'],
            'max_drawdown_pct': metrics.max_drawdown_pct['pct'],
            'num_trades': len(metrics.trade_history),
        })
    return pd.DataFrame(rows)


# sensible default grids per parameter (slippage in bps, fee as a rate)
_DEFAULT_VALUES = {
    'slippage_bps': [0, 2.5, 5, 10, 20, 40, 80],
    'fee_rate': [0.0, 0.0005, 0.001, 0.002, 0.004, 0.008],
}


def main():
    from backtest.__main__ import load_config, validate_config, resolve

    parser = argparse.ArgumentParser(
        prog='backtest.cost_sweep',
        description='Sweep a transaction-cost parameter and report metric sensitivity.')
    parser.add_argument('config', help='config module name in configs/')
    parser.add_argument('--param', default='slippage_bps', choices=list(_DEFAULT_VALUES),
                        help='cost parameter to sweep')
    parser.add_argument('--values', type=float, nargs='+',
                        help='cost values to test (default depends on --param)')
    parser.add_argument('--metric', default='total_return', help='metric to plot vs cost')
    parser.add_argument('--plot', action='store_true', help='show the sensitivity chart')
    parser.add_argument('--save', metavar='PATH', help='save the chart to a file')
    args = parser.parse_args()

    config = load_config(args.config)
    config['name'] = args.config
    validate_config(config)
    resolve(config)

    values = args.values if args.values is not None else _DEFAULT_VALUES[args.param]
    table = sweep_costs(config, args.param, values)
    print(table.to_string(index=False))

    if args.plot or args.save:
        import matplotlib.pyplot as plt
        from metrics.plots import plot_cost_sweep
        fig = plot_cost_sweep(table, args.param, args.metric)
        if args.save:
            fig.savefig(args.save, dpi=120, bbox_inches='tight')
            print(f'saved plot to {args.save}')
        if args.plot:
            plt.show()


if __name__ == '__main__':
    main()
