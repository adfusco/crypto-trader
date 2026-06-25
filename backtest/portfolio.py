class Portfolio:
    """Tracks cash, open positions, P&L, and the equity curve over a backtest.

    Sign convention: a position's ``qty`` is signed — positive for long, negative
    for short. Cash is debited/credited by ``signed_qty * price`` on every fill, so
    a short *adds* its proceeds to cash and carries a negative holding value. Equity
    is therefore ``cash + signed market value of holdings`` and stays correct for
    longs and shorts alike (see ``mark_to_market``). Each open position also stores
    its accrued entry ``fee``, prorated when the position is partially closed.
    """

    def __init__(self, logger, init_cash=100000.0):
        self.init_capital = init_cash
        self.cash = init_cash
        self.max_equity = self.cash
        self.equity = self.cash
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.net_pnl = 0.0
        self.total_fees = 0.0

        self.open_positions = {}
        self.trade_history = []
        self.position_history = []
        self.fill_log = []

        self.equity_curve = []
        self.drawdowns = []
        self.timestamps = []

        self.max_drawdown_amt = {'amt': 0.0, 'pct': 0.0}
        self.max_drawdown_pct = {'pct': 0.0, 'amt': 0.0}
        self.leverage_used = 0.0
        self.position_exposure = {}

        self.logger = logger

    def record_trade(self, trade_dict):
        self.trade_history.append(trade_dict)

    def _avg_entry_price(self, old_qty, old_price, new_qty, new_price):
        return (abs(old_qty) * old_price + abs(new_qty) * new_price) / (abs(old_qty) + abs(new_qty))

    def _update_position(self, timestamp, symbol, side, qty, fill_price, fee):
        """Apply one fill to ``symbol``'s position and update cash, fees, and P&L.

        Three cases, by the sign of the incoming order relative to the held qty:
          - no position -> open a new one
          - same direction -> extend, averaging the entry price
          - opposite direction -> close up to ``|old_qty|`` units, realizing P&L on
            just the closed portion; any remainder is a smaller same-side position
            or, if the order overshoots, a reversal into a fresh opposite position.
        ``fee`` is the incoming order's fee; on a close it is split between the
        closed units and (for a reversal) the units left open, and the old entry
        fee is prorated the same way.
        """
        existing = self.open_positions.get(symbol)
        direction = (1 if side == 'long' else -1)
        signed_qty = qty * direction

        self.cash -= fee
        self.total_fees += fee

        if existing is None:
            self.cash -= signed_qty * fill_price
            self.open_positions[symbol] = {
                'entry_timestamp': timestamp,
                'entry_price': fill_price,
                'fee': fee,
                'qty': signed_qty,
                'side': side,
            }

        elif existing['qty'] * signed_qty > 0:
            # same direction: average the entry, accrue the fee
            old_qty = existing['qty']
            self.cash -= signed_qty * fill_price
            existing['qty'] = old_qty + signed_qty
            existing['entry_price'] = self._avg_entry_price(old_qty, existing['entry_price'], signed_qty, fill_price)
            existing['fee'] = existing['fee'] + fee

        else:
            old_qty = existing['qty']
            old_dir = 1 if old_qty > 0 else -1
            closed_qty = min(abs(old_qty), abs(signed_qty))  # positive magnitude
            closed_signed = closed_qty * old_dir

            closing_fee = (closed_qty / abs(signed_qty)) * fee
            old_closing_fee = (closed_qty / abs(old_qty)) * existing['fee']

            self.cash += closed_signed * fill_price
            realized_pnl = closed_signed * (fill_price - existing['entry_price'])
            net_pnl = realized_pnl - (closing_fee + old_closing_fee)
            self.realized_pnl += realized_pnl
            self.net_pnl += net_pnl

            trade_dict = {
                'entry_timestamp': existing['entry_timestamp'],
                'exit_timestamp': timestamp,
                'entry_price': existing['entry_price'],
                'exit_price': fill_price,
                'qty': closed_signed,
                'side': 'long' if old_qty > 0 else 'short',
                'pnl': net_pnl,
            }
            self.record_trade(trade_dict)
            self.logger.log_trade(trade_dict)

            new_qty = old_qty + signed_qty
            if new_qty == 0:
                self.open_positions.pop(symbol)
            elif old_qty * new_qty > 0:
                # partial close: remainder keeps its entry price, drops the closed fee
                existing['qty'] = new_qty
                existing['fee'] = existing['fee'] - old_closing_fee
            else:
                # reversal: leftover qty opens a fresh opposite position
                self.cash -= new_qty * fill_price
                self.open_positions[symbol] = {
                    'entry_timestamp': timestamp,
                    'entry_price': fill_price,
                    'fee': fee - closing_fee,
                    'qty': new_qty,
                    'side': side,
                }

    def record_pos_snapshot(self, timestamp):
        snapshot = {
            'timestamp': timestamp,
            'cash': self.cash,
            'equity': self.get_equity()
        }
        for symbol, pos in self.open_positions.items():
            snapshot[symbol] = {
                'qty': pos['qty'],
                'entry_price': pos['entry_price']
            }
        self.position_history.append(snapshot)

    def update_with_fill(self, fill):
        ts = fill.get('timestamp')
        symbol = fill.get('symbol')
        side = fill.get('side')
        qty = fill.get('qty')
        fee = fill.get('fee')
        exec_price = fill.get('execution_price')

        self.fill_log.append(fill)
        self._update_position(ts, symbol, side, qty, exec_price, fee)
        self.record_pos_snapshot(ts)

    def mark_to_market(self, row, price_col, timestamp):
        """Revalue open positions at ``row``'s prices and append one point to the
        equity / drawdown curves.

        Equity is ``cash + signed market value`` (not ``cash + unrealized P&L``):
        cash already holds each position's entry cost/proceeds, so the holdings'
        current market value is what gets added back. ``unrealized_pnl`` is reported
        separately as the true gain over entry. Raises if a held symbol has no price
        in the row.
        """
        self.unrealized_pnl = 0.0
        self.timestamps.append(timestamp)

        total_market_value = 0.0  # signed value of holdings
        total_pos_value = 0.0     # gross (absolute) exposure
        pos_values = {}
        for symbol, pos in self.open_positions.items():
            live_price = row.get(f'{symbol}_{price_col}')
            if live_price is None:
                raise ValueError(f'no price for symbol {symbol}')
            qty = pos['qty']

            self.unrealized_pnl += (live_price - pos['entry_price']) * qty

            pos_value = live_price * qty
            total_market_value += pos_value
            total_pos_value += abs(pos_value)
            pos_values[symbol] = abs(pos_value)

        self.equity = self.cash + total_market_value
        self.max_equity = max(self.max_equity, self.equity)
        self.leverage_used = total_pos_value / self.equity if self.equity else 0.0
        self.position_exposure = {
            pos: (value / self.equity if self.equity else 0.0)
            for pos, value in pos_values.items()
        }

        drawdown_amt = self.max_equity - self.equity
        drawdown_pct = drawdown_amt / self.max_equity

        if drawdown_amt > self.max_drawdown_amt['amt']:
            self.max_drawdown_amt = {'amt': drawdown_amt, 'pct': drawdown_pct}
        if drawdown_pct > self.max_drawdown_pct['pct']:
            self.max_drawdown_pct = {'pct': drawdown_pct, 'amt': drawdown_amt}

        self.drawdowns.append({
            'timestamp': timestamp,
            'drawdown_amt': drawdown_amt,
            'drawdown_pct': drawdown_pct,
            'equity': self.equity,
            'peak': self.max_equity
        })

        equity_dict = {
            'timestamp': timestamp,
            'equity': self.equity,
            'cash': self.cash,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl
        }
        self.equity_curve.append(equity_dict)
        self.logger.log_portfolio_update(equity_dict)

    def get_equity(self):
        return self.equity

    def get_position(self, symbol):
        return self.open_positions.get(symbol)

    def get_stats(self):
        return {
            'cash': self.cash,
            'equity': self.equity,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
        }
