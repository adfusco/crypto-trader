from backtest.portfolio import Portfolio
from backtest.logger import NullLogger

TS = '2022-01-01'


def _fill(side, qty, price, fee, symbol='X/USDT'):
    return {'timestamp': TS, 'symbol': symbol, 'side': side, 'qty': qty,
            'fee': fee, 'execution_price': price, 'order_type': 'market'}


def _portfolio():
    return Portfolio(NullLogger(), init_cash=100000.0)


def test_fresh_long_open_deducts_cost_and_fee():
    p = _portfolio()
    p.update_with_fill(_fill('long', 10, 100.0, 5.0))
    assert p.cash == 100000.0 - 1000.0 - 5.0  # 98995
    assert p.total_fees == 5.0
    assert p.open_positions['X/USDT']['qty'] == 10


def test_mark_to_market_equity_is_cash_plus_position_value():
    p = _portfolio()
    p.update_with_fill(_fill('long', 10, 100.0, 5.0))
    p.mark_to_market({'timestamp': TS, 'X/USDT_close': 100.0}, 'close', TS)
    # equity = cash(98995) + 10*100 = 99995 (down only by the fee)
    assert p.equity == 99995.0


def test_drawdown_tracked_on_markdown():
    p = _portfolio()
    p.update_with_fill(_fill('long', 10, 100.0, 0.0))
    p.mark_to_market({'timestamp': TS, 'X/USDT_close': 100.0}, 'close', TS)  # equity 100000
    p.mark_to_market({'timestamp': TS, 'X/USDT_close': 90.0}, 'close', TS)   # equity 99900
    assert p.max_drawdown_amt['amt'] == 100.0


def test_full_close_realizes_pnl_and_records_trade():
    p = _portfolio()
    p.update_with_fill(_fill('long', 10, 100.0, 5.0))
    p.update_with_fill(_fill('short', 10, 110.0, 5.5))  # close
    assert p.realized_pnl == 100.0  # 10 * (110 - 100)
    assert len(p.trade_history) == 1
    # net pnl = gross 100 - (closing_fee 5.5 + entry_fee 5.0)
    assert p.trade_history[0]['pnl'] == 89.5
    assert 'X/USDT' not in p.open_positions


def test_short_position_profits_when_price_falls():
    p = _portfolio()
    p.update_with_fill(_fill('short', 10, 100.0, 0.0))
    p.update_with_fill(_fill('long', 10, 90.0, 0.0))  # cover
    assert p.realized_pnl == 100.0  # short from 100, covered at 90


def test_partial_close_realizes_pnl_on_closed_units_only():
    # long 10 @ 100, then sell 4 @ 110 -> realize 4 units, keep long 6
    p = _portfolio()
    p.update_with_fill(_fill('long', 10, 100.0, 5.0))
    p.update_with_fill(_fill('short', 4, 110.0, 2.0))

    pos = p.open_positions['X/USDT']
    assert pos['qty'] == 6              # still long the remaining 6
    assert pos['entry_price'] == 100.0  # entry price of the remainder unchanged
    # closed entry-fee share = (4/10)*5 = 2.0 -> remaining fee 3.0
    assert abs(pos['fee'] - 3.0) < 1e-9
    assert p.realized_pnl == 40.0       # 4 * (110 - 100)
    # net pnl = 40 - (incoming closing fee 2.0 + old fee share 2.0)
    assert abs(p.trade_history[0]['pnl'] - 36.0) < 1e-9


def test_adding_same_side_averages_entry_and_accrues_fee():
    # long 10 @ 100, then long 5 @ 110 -> avg entry, no realized pnl
    p = _portfolio()
    p.update_with_fill(_fill('long', 10, 100.0, 5.0))
    p.update_with_fill(_fill('long', 5, 110.0, 2.0))

    pos = p.open_positions['X/USDT']
    assert pos['qty'] == 15
    assert abs(pos['entry_price'] - (10 * 100 + 5 * 110) / 15) < 1e-9
    assert pos['fee'] == 7.0
    assert p.realized_pnl == 0.0
    assert len(p.trade_history) == 0


def test_reversal_prorates_fees_by_closed_fraction():
    # long 10 @ 100, then short 25 @ 110 -> close 10, open short 15
    p = _portfolio()
    p.update_with_fill(_fill('long', 10, 100.0, 5.0))
    p.update_with_fill(_fill('short', 25, 110.0, 13.75))

    pos = p.open_positions['X/USDT']
    assert pos['qty'] == -15  # flipped to short 15
    # close_frac = 10/25 = 0.4 -> new entry fee = 0.6 * 13.75 = 8.25
    assert abs(pos['fee'] - 8.25) < 1e-9
    # realized trade: gross 100 - (closing_fee 0.4*13.75=5.5 + entry_fee 5.0) = 89.5
    assert abs(p.trade_history[0]['pnl'] - 89.5) < 1e-9
