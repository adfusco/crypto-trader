class Portfolio:
    def __init__(self, init_cash=100000.0):
        self.init_capital = init_cash
        self.cash = init_cash
        self.max_equity = self.cash
        self.equity = self.cash
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.total_fees = 0.0

        self.open_positions = {}
        self.trade_history = []
        self.position_history = []
        self.fill_log = []

        self.equity_curve = []
        self.drawdowns = []
        self.timestamps = []

        self.max_drawdown = 0.0
        self.leverage_used = 0.0
        self.position_exposure = {}

    def record_trade(self, fill):
        self.trade_history.append(fill)

    def _avg_entry_price(self, old_qty, old_price, new_qty, new_price):
        return (abs(old_qty) * old_price + abs(new_qty) * new_price) / (abs(old_qty) + abs(new_qty))

    def _update_position(self, symbol, side, qty, fill_price, fee):
        existing = self.open_positions.get(symbol)
        direction = (1 if side == 'buy' else -1)
        signed_qty = qty * direction

        self.cash -= fee
        self.total_fees += fee

        if existing is None:
            self.open_positions[symbol] = {
                'entry_price':fill_price,
                'qty':signed_qty
            }
            self.cash -= signed_qty * fill_price

        else:
            old_qty = existing['qty']
            new_qty = old_qty + signed_qty
            old_entry_price = existing['entry_price']

            same_side = (old_qty * new_qty > 0)

            if same_side:
                existing['qty'] = new_qty
                existing['entry_price'] = self._avg_entry_price(old_qty, old_entry_price, signed_qty, fill_price)
                self.cash -= signed_qty * fill_price

            else:
                realized_qty = min(abs(old_qty), abs(signed_qty))
                pnl_per_unit = (fill_price-old_entry_price)
                realized_pnl = realized_qty * pnl_per_unit

                if side == 'buy': realized_pnl *= -1
                self.realized_pnl += realized_pnl
                self.cash += realized_qty * fill_price * (-1 if side == 'buy' else 1)

                remaining_qty = new_qty
                if remaining_qty == 0: self.open_positions.pop(symbol)
                else:
                    self.open_positions[symbol] = {
                        'qty':remaining_qty,
                        'entry_price':fill_price
                    }
                    self.cash -= signed_qty * fill_price

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

        self.record_trade(fill)
        self._update_position(symbol, side, qty, exec_price, fee)
        self.record_pos_snapshot(ts)

    def mark_to_market(self, prices, timestamp):
        self.unrealized_pnl = 0
        self.equity = self.cash
        self.timestamps.append(timestamp)

        for symbol, pos in self.open_positions.items():
            live_price = prices.get(symbol)
            if live_price is None:
                raise ValueError(f'no price for symbol {symbol}')

            price = pos['entry_price']
            qty = pos['qty']

            unrealized = (live_price - price) * qty
            self.unrealized_pnl += unrealized
            self.equity += unrealized

        total_pos_value = 0
        for symbol, pos in self.open_positions.items():
            price = pos['entry_price']
            qty = pos['qty']
            pos_value = price*qty
            total_pos_value += abs(pos_value)

            self.position_exposure[symbol] = abs(pos_value) / self.equity

        self.max_equity = max(self.max_equity, self.equity)
        self.leverage_used = total_pos_value / self.equity

        drawdown_amt = self.max_equity - self.equity
        drawdown_pct = drawdown_amt / self.max_equity

        self.drawdowns.append({
            'timestamp': timestamp,
            'drawdown_amt': drawdown_amt,
            'drawdown_pct': drawdown_pct,
            'equity': self.equity,
            'peak': self.max_equity
        })

        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': self.equity,
            'cash': self.cash,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl
        })

    def get_equity(self):
        return self.equity

    def get_position(self, symbol):
        return self.open_positions.get(symbol)

    def get_stats(self):
        return {
            'cash':self.cash,
            'equity':self.equity,
            'realized_pnl':self.realized_pnl,
            'unrealized_pnl':self.unrealized_pnl
        }

    def reset(self):
        self.__init__(self.init_capital)
