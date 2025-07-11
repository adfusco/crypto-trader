#simulates fills, slippage, latency, etc.
class DummySimulator:
    def __init__(self, slippage_bps=0.0, fee_rate=0.005):
        self.slippage_bps = slippage_bps
        self.fee_rate = fee_rate

    def simulate_order(self, order, candle_row):
        ts = candle_row['timestamp']
        symbol = order['symbol']
        side = order['side']
        qty = order['qty']
        order_type = order['order_type']

        price_col = 'close'
        raw_price = candle_row[f'{symbol}_{price_col}']

        slip = (raw_price * self.slippage_bps) / 10000
        direction = 1 if side == 'buy' else -1
        exec_price = raw_price + (slip*direction)

        fee = self.fee_rate * exec_price * qty

        return {
            'timestamp':ts,
            'symbol':symbol,
            'side':side,
            'qty':qty,
            'raw_price':raw_price,
            'execution_price':exec_price,
            'fee':fee,
            'order_type':order_type
        }
