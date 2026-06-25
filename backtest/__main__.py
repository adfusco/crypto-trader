"""Single CLI entry point: python -m backtest <config_name>

Loads configs/<config_name>.py, resolves the strategy (and objective) from the
registries, and dispatches by the config's 'mode' key.
"""
import argparse
import importlib
import pickle

import pandas as pd

from strategies.registry import STRATEGY_REGISTRY
from backtest.run import run_backtest
from backtest.walk_forward import walk_forward, OBJECTIVE_REGISTRY
from metrics.metrics import Metrics
from metrics.plots import plot_performance


def load_config(name):
    module = importlib.import_module(f'configs.{name}')
    return dict(module.config)


# keys every config needs, plus the keys specific to each mode. Plumbing paths
# (merged data, log dir, save dir) are derived from the config name, not required.
_COMMON_KEYS = ['strategy', 'symbols', 'timeframe', 'init_cash', 'slippage_bps']
_MODE_KEYS = {
    'backtest': ['strategy_params'],
    'walkforward': ['base_params', 'param_grid', 'train_size', 'test_size', 'step'],
}


def validate_config(config):
    """Fail fast with a clear message on missing keys or unknown registry names,
    rather than a deep KeyError mid-run."""
    mode = config.get('mode')
    if mode not in _MODE_KEYS:
        raise ValueError(f"config 'mode' must be one of {list(_MODE_KEYS)}, got {mode!r}")

    required = _COMMON_KEYS + _MODE_KEYS[mode]
    if config.get('fetch', False):  # fetching needs a start date to pull from
        required += ['start']
    missing = [k for k in required if k not in config]
    if missing:
        raise ValueError(f"config (mode={mode}) missing required keys: {missing}")

    if config['strategy'] not in STRATEGY_REGISTRY:
        raise ValueError(f"unknown strategy {config['strategy']!r}; "
                         f"known: {list(STRATEGY_REGISTRY)}")
    if 'objective' in config and config['objective'] not in OBJECTIVE_REGISTRY:
        raise ValueError(f"unknown objective {config['objective']!r}; "
                         f"known: {list(OBJECTIVE_REGISTRY)}")


def resolve(config):
    config['strategy_class'] = STRATEGY_REGISTRY[config['strategy']]
    if 'objective' in config:
        config['objective'] = OBJECTIVE_REGISTRY[config['objective']]
    return config


def _run_walkforward(config, name):
    result = walk_forward(config)
    print(pd.DataFrame(result['folds']).to_string(index=False))
    save_path = f"{config['portfolio_save_dir']}/{name}.pkl"
    with open(save_path, 'wb') as f:
        pickle.dump(result['oos_data'], f)
    return result['oos_data'], save_path


def _report(portfolio_data, save_path, name, do_plot):
    print()
    Metrics(portfolio_data).print_stats()
    print(f'\nsaved:  {save_path}')
    print(f'replot: python -m metrics.metrics_engine {name}')
    if do_plot:
        import matplotlib.pyplot as plt
        plot_performance(Metrics(portfolio_data))
        plt.show()


def main():
    parser = argparse.ArgumentParser(description='Run a backtest or walk-forward from a config.')
    parser.add_argument('config', help='config module name in configs/ (e.g. mr_basic_backtest)')
    parser.add_argument('--fetch', action='store_true', help='re-download data before running')
    parser.add_argument('--plot', action='store_true', help='show the equity/drawdown chart')
    args = parser.parse_args()

    config = load_config(args.config)
    config['name'] = args.config
    if args.fetch:
        config['fetch'] = True
    validate_config(config)
    resolve(config)

    if config['mode'] == 'backtest':
        portfolio_data, save_path = run_backtest(config)
    else:  # validate_config guarantees mode is 'backtest' or 'walkforward'
        portfolio_data, save_path = _run_walkforward(config, args.config)

    _report(portfolio_data, save_path, args.config, args.plot)


if __name__ == '__main__':
    main()
