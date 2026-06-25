from strategies.base import Strategy
from backtest.utils.circular_buffer import CircularBuffer
import feature_engineering.feature_functions as ffs

class MeanReversionBasic(Strategy):
    @classmethod
    def default_params(cls):
        return {
            'use_precomputed_features': True,
            'symbol': None,
            'window': 20,
            'price_col': 'close',
            'risk_pct': 0.02,
            'zscores': {'long_entry': -1, 'long_exit': -1, 'short_entry': 1, 'short_exit': 1}
        }

    def __init__(self, params: dict):
        super().__init__(params)
        self.required_features = {'zscore': {'window': self.params['window'], 'price_col': self.params['price_col']}}

        precomputed = self.params['use_precomputed_features']
        if not precomputed:
            self.prices = CircularBuffer(size=self.params['window'])

    def update_state(self, candle_row, open_positions=None):
        precomputed = self.params['use_precomputed_features']
        symbol = self.params['symbol']

        if precomputed:
            self.state['zscore'] = candle_row[f'{symbol}_zscore']
        else:
            price_col = self.params['price_col']
            price = candle_row[f"{symbol}_{price_col}"]
            self.prices.append(price)
            self.state['zscore'] = ffs.zscore(self.prices.to_array())

        if open_positions:
            side = open_positions[next(iter(open_positions))]['side']
            valid_sides = {'long', 'short'}
            if side in valid_sides:
                self.state['position'] = side
            else:
                raise ValueError('invalid position')
        else:
            self.state['position'] = None

    def gen_signal(self):
        pos = self.state['position']
        z = self.state['zscore']

        z_long_entry = self.params['zscores']['long_entry']
        z_long_exit = self.params['zscores']['long_exit']
        z_short_entry = self.params['zscores']['short_entry']
        z_short_exit = self.params['zscores']['short_exit']

        long_entry = z < z_long_entry
        long_exit = z > z_long_exit
        short_entry = z > z_short_entry
        short_exit = z < z_short_exit

        if pos is None:
            if long_entry:
                return {'side': 'long', 'order_type': 'market'}
            elif short_entry:
                return {'side': 'short', 'order_type': 'market'}

        elif pos == 'long' and long_exit:
            return {'side': 'short', 'order_type': 'market'}
        elif pos == 'short' and short_exit:
            return {'side': 'long', 'order_type': 'market'}

        return {'side': 'hold'}

    def gen_order(self, signal, row, portfolio):
        order_dict = {}
        if signal['side'] == 'hold':
            return order_dict

        equity = portfolio.get_equity()
        risk_pct = self.params['risk_pct']
        price_col = self.params['price_col']

        symbol = self.params['symbol']
        price = row[f'{symbol}_{price_col}']
        qty = int(equity * risk_pct / price)
        if qty > 0:
            order_dict[symbol] = {
                'side': signal['side'],
                'qty': qty,
                'order_type': signal['order_type'],
            }

        return order_dict