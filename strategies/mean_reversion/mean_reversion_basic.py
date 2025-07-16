from strategies.base import Strategy
from backtest.utils.circular_buffer import CircularBuffer
import feature_engineering.feature_functions as ffs

class MeanReversionBasic(Strategy):
    @staticmethod
    def required_params():
        return ['use_precomputed_features', 'symbol', 'window', 'price_col', 'zscores']

    @classmethod
    def default_params(cls):
        return {
            'use_precomputed_features':True,
            'symbol':None,
            'window':20,
            'price_col':'close',
            'zscores':{'entry_long':-1, 'exit_long':-1, 'entry_short':1, 'exit_short':1}
        }

    def __init__(self, params: dict):
        super().__init__(params)
        self.required_features = {'zscore': {'window':self.params['window'], 'price_col':self.params['price_col']}}
        self.prices = CircularBuffer(size=self.params['window'])

    def update_state(self, candle_row, open_positions=None):
        symbol = self.params['symbol']
        price_col = self.params['price_col']
        price = candle_row[f"{symbol}_{price_col}"]
        self.prices.append(price)

        precomputed = self.params['use_precomputed_features']
        if precomputed:
            self.state['zscore'] = candle_row[f'{symbol}_zscore']
        else:
            self.state['zscore'] = ffs.zscore(self.prices.to_array())

        if open_positions:
            position = open_positions[next(iter(open_positions))]['side']
            valid_positions = {'long', 'short'}
            if position in valid_positions:
                self.state['position'] = position
            else:
                raise ValueError('invalid position')

    def gen_signal(self):
        pos = self.state.get('position')
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
                return {'side':'long', 'order_type':'market'}
            elif short_entry:
                return {'side':'short', 'order_type':'market'}

        elif pos == 'long' and long_exit:
            return {'side':'short', 'order_type':'market'}
        elif pos == 'short' and short_exit:
            return {'side':'long', 'order_type':'market'}

        return {'side':'hold'}

    def gen_order(self, signal):
        if signal['side'] == 'hold': return None
        symbol = self.params['symbol']
        qty = 1

        return {
            'symbol':symbol,
            'side':signal['side'],
            'qty':qty,
            'order_type':signal['order_type'],
        }

    def reset(self):
        self.state.clear()