class Portfolio:
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

        self.max_drawdown_amt = {'amt':0.0, 'pct':0.0}
        self.max_drawdown_pct = {'pct':0.0, 'amt':0.0}
        self.leverage_used = 0.0
        self.position_exposure = {}

        self.logger = logger

    def record_trade(self, trade_dict):
        self.trade_history.append(trade_dict)

    def _avg_entry_price(self, old_qty, old_price, new_qty, new_price):
        return (abs(old_qty) * old_price + abs(new_qty) * new_price) / (abs(old_qty) + abs(new_qty))

    def _update_position(self, timestamp, symbol, side, qty, fill_price, fee):
        existing = self.open_positions.get(symbol)
        direction = (1 if side == 'long' else -1)
        signed_qty = qty * direction

        self.cash -= fee
        self.total_fees += fee

        if existing is None:
            self.cash -= signed_qty * fill_price
            self.open_positions[symbol] = {
                'entry_timestamp':timestamp,
                'entry_price':fill_price,
                'fee':fee,
                'qty':signed_qty,
                'side':side
            }

        else:
            old_qty = existing['qty']
            new_qty = old_qty + signed_qty
            old_entry_price = existing['entry_price']
            old_timestamp = existing['entry_timestamp']
            old_fee = existing['fee']
            closing_fee = (old_qty / abs(signed_qty)) * fee
            new_entry_fee = 1 - (old_qty / abs(signed_qty)) * fee

            same_side = (old_qty * new_qty > 0)

            if same_side:
                self.cash -= signed_qty * fill_price
                existing['qty'] = new_qty
                existing['entry_price'] = self._avg_entry_price(old_qty, old_entry_price, signed_qty, fill_price)

            else:
                realized_qty = old_qty # = min(abs(old_qty), abs(signed_qty)) before for safety
                self.cash += realized_qty * fill_price
                pnl_per_unit = (fill_price-old_entry_price)
                realized_pnl = realized_qty * pnl_per_unit
                net_pnl = realized_pnl - (closing_fee + old_fee)
                self.net_pnl += net_pnl
                self.realized_pnl += realized_pnl

                trade_dict = {
                    'entry_timestamp': old_timestamp,
                    'exit_timestamp':timestamp,
                    'entry_price':old_entry_price,
                    'exit_price':fill_price,
                    'qty':realized_qty,
                    'side': 'long' if old_qty > 0 else 'short',
                    'pnl':net_pnl
                }
                self.record_trade(trade_dict)
                self.logger.log_trade(trade_dict)

                remaining_qty = new_qty
                if remaining_qty == 0: self.open_positions.pop(symbol)
                else:
                    self.cash -= remaining_qty * fill_price
                    self.open_positions[symbol] = {
                        'entry_timestamp':timestamp,
                        'entry_price':fill_price,
                        'fee':new_entry_fee,
                        'qty':remaining_qty,
                        'side': side
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
        self.unrealized_pnl = 0.0
        self.timestamps.append(timestamp)

        total_pos_value = 0
        pos_values = {}
        for symbol, pos in self.open_positions.items():
            live_price = row.get(f'{symbol}_{price_col}')
            if live_price is None:
                raise ValueError(f'no price for symbol {symbol}')
            qty = pos['qty']

            unrealized = live_price * qty
            self.unrealized_pnl += unrealized

            pos_value = live_price * qty
            total_pos_value += abs(pos_value)
            pos_values[symbol] = abs(pos_value)

        self.equity = self.cash + self.unrealized_pnl
        self.max_equity = max(self.max_equity, self.equity)
        self.leverage_used = total_pos_value / self.equity
        self.position_exposure = {pos: value / self.equity for pos, value in pos_values.items()}

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

        #print debugger
        #symbol_print = 'ETH/USDT'
        #print(f"[{timestamp}] live price: {row.get(f'{symbol_print}_{price_col}')}, cash: {self.cash:.2f}, unrealized: {self.unrealized_pnl:.2f}, equity: {self.equity:.2f}, open_positions: {len(self.open_positions)}")

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
