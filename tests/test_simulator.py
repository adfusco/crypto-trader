from backtest.simulator import DummySimulator


def _row(open_price):
    return {'timestamp': '2022-01-01', 'X/USDT_open': open_price}


def test_long_slippage_raises_exec_price():
    sim = DummySimulator(slippage_bps=10, fee_rate=0.0)
    fills = sim.simulate_orders({'X/USDT': {'side': 'long', 'qty': 1, 'order_type': 'market'}}, _row(100.0))
    # 10 bps of 100 = 0.10, added for a buy
    assert fills[0]['execution_price'] == 100.10


def test_short_slippage_lowers_exec_price():
    sim = DummySimulator(slippage_bps=10, fee_rate=0.0)
    fills = sim.simulate_orders({'X/USDT': {'side': 'short', 'qty': 1, 'order_type': 'market'}}, _row(100.0))
    assert fills[0]['execution_price'] == 99.90


def test_fee_is_rate_times_notional():
    sim = DummySimulator(slippage_bps=0, fee_rate=0.0005)
    fills = sim.simulate_orders({'X/USDT': {'side': 'long', 'qty': 4, 'order_type': 'market'}}, _row(100.0))
    # fee = 0.0005 * exec_price(100) * qty(4) = 0.20
    assert abs(fills[0]['fee'] - 0.20) < 1e-12
