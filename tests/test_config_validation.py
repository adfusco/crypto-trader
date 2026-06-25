import pytest

from backtest.__main__ import validate_config


def _backtest_config(**overrides):
    config = {
        'mode': 'backtest',
        'strategy': 'mr_basic',
        'strategy_params': {},
        'symbols': ['ETH/USDT'],
        'timeframe': '1d',
        'path_to_csvs': 'x',
        'path_to_merged_data': 'y',
        'log_dir': 'logs',
        'init_cash': 100000.0,
        'slippage_bps': 5,
        'portfolio_save_dir': 'out',
        'fetch': False,  # so limit/since_ms aren't required
    }
    config.update(overrides)
    return config


def test_valid_backtest_config_passes():
    validate_config(_backtest_config())  # no raise


def test_missing_key_is_reported():
    config = _backtest_config()
    del config['init_cash']
    with pytest.raises(ValueError, match='init_cash'):
        validate_config(config)


def test_unknown_strategy_is_reported():
    with pytest.raises(ValueError, match='unknown strategy'):
        validate_config(_backtest_config(strategy='nope'))


def test_unknown_mode_is_reported():
    with pytest.raises(ValueError, match="mode"):
        validate_config(_backtest_config(mode='liveTrade'))


def test_fetch_true_requires_start():
    config = _backtest_config(fetch=True)  # start now required, absent
    with pytest.raises(ValueError, match='start'):
        validate_config(config)


def test_walkforward_requires_grid_and_windows():
    config = {
        'mode': 'walkforward', 'strategy': 'mr_multi', 'symbols': ['ETH/USDT'],
        'timeframe': '1d', 'path_to_csvs': 'x', 'path_to_merged_data': 'y',
        'init_cash': 100000.0, 'slippage_bps': 5, 'portfolio_save_dir': 'out', 'fetch': False,
        # missing base_params, param_grid, train_size, test_size, step
    }
    with pytest.raises(ValueError, match='param_grid|base_params|train_size'):
        validate_config(config)
