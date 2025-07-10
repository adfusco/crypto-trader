class Portfolio:
    def __init__(self, init_cash=100000.0):
        self.cash = init_cash
        self.equity = self.cash
        self.open_positions = {}
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.total_value = self.cash

        self.trade_history = []
        self.position_history = []
        self.fill_log = []

        #self.equity_curve = []
        #self.drawdowns = []
        #self.timestamps = []

        #self.max_drawdown = 0.0
        #self.leverage_used = 0.0 position size vs cash
        #self.position_exposure = {} % of equity per symbol
        #self.num_open_positions = 0

    def record_trade(self, fill):
        self.trade_history.append(fill)

    def update_position(self, symbol, side, qty, execution_price):
       pos = self.open_positions.get(symbol)

       if pos is None:
           self.open_positions[symbol] = {
               'entry_price':execution_price,
               'qty':(qty if side == 'buy' else -1*qty)
           }

       else:
           old_qty = pos['qty']
           old_entry_price = pos['entry_price']

           #must finish...


    def update_with_fill(self, fill):
        ts = fill.get('timestamp')
        symbol = fill.get('symbol')
        side = fill.get('side')
        qty = fill.get('qty')
        order_type = fill.get('order_type')
        raw_price = fill.get('raw_price')
        fee = fill.get('fee')
        exec_price = fill.get('execution_price')

        self.record_trade(fill)
        self.update_position(symbol, side, qty, exec_price)
        self.record_pos_snapshot(ts)

    def mark_to_market(self):
        pass

    def record_pos_snapshot(self, timestamp):
        snapshot = {
            'timestamp':timestamp,
            'cash':self.cash,
            'equity':self.get_equity()
        }
        for symbol, pos in self.open_positions.items():
            snapshot[symbol] = {
                'qty': pos['qty'],
                'execution_price': pos['execution_price']
            }
        self.position_history.append(snapshot)

    def get_equity(self):
        return self.equity

    def get_position(self, symbol):
        return self.open_positions.get(symbol)

    def get_stats(self):
        return {
            'cash':self.cash,
            'equity':self.equity,
            'realized_pnl':self.realized_pnl,
            'unrealized_pnl':self.unrealized_pnl,
            'total_value':self.total_value
        }

    def reset(self):
        pass



