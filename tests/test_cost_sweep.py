from backtest.cost_sweep import sweep_costs
from backtest.__main__ import load_config, resolve
from metrics.plots import _breakeven_cost


def test_breakeven_cost_interpolates_zero_crossing():
    # return goes +1 -> -1 between cost 10 and 20, crossing zero at the midpoint
    assert _breakeven_cost([0, 10, 20], [2.0, 1.0, -1.0]) == 15.0


def test_breakeven_cost_none_when_never_negative():
    assert _breakeven_cost([0, 10, 20], [3.0, 2.0, 1.0]) is None


def test_sweep_costs_columns_and_monotonic_in_slippage():
    config = resolve(load_config('mr_basic_backtest'))
    config['name'] = 'mr_basic_backtest'
    table = sweep_costs(config, 'slippage_bps', values=[0, 50])

    assert list(table['slippage_bps']) == [0, 50]
    assert {'total_return', 'sharpe_ratio', 'profit_factor', 'num_trades'} <= set(table.columns)
    # more slippage cannot improve the return
    assert table.iloc[1]['total_return'] <= table.iloc[0]['total_return']
