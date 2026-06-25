# Simulates fills: applies slippage and fees to fill each order at the bar's open.
class DummySimulator:
    def __init__(self, slippage_bps=0.0, fee_rate=0.0005):
        self.slippage_bps = slippage_bps
        self.fee_rate = fee_rate

    def simulate_orders(self, orders, candle_row):
        ts = candle_row['timestamp']
        fills = []

        for symbol, order in orders.items():
            side = order['side']
            qty = order['qty']
            order_type = order['order_type']

            raw_price = candle_row[f'{symbol}_open']

            slip = (raw_price * self.slippage_bps) / 10000
            direction = 1 if side == 'long' else -1
            exec_price = raw_price + (slip * direction)

            fee = self.fee_rate * exec_price * qty

            fills.append({
                'timestamp': ts,
                'symbol': symbol,
                'side': side,
                'qty': qty,
                'raw_price': raw_price,
                'execution_price': exec_price,
                'fee': fee,
                'order_type': order_type,
            })

        return fills