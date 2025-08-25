from strategies.base import Strategy
from backtest.utils.circular_buffer import CircularBuffer
import feature_engineering.feature_functions as ffs

class MeanReversionPair(Strategy):
    @staticmethod
    def required_params():
        return ['use_precomputed_features', 'symbols', 'window', 'price_col', 'zscores']

    @classmethod
    def default_params(cls):
        return {
            'use_precomputed_features':True,
            'symbols':None,
            'window':20,
            'price_col':'close',
            'zscores':{'entry_long':-1, 'exit_long':-1, 'entry_short':1, 'exit_short':1}
        }

    def __init__(self, params: dict):
        super().__init__(params)
        self.required_features = {'zscore': {'window':self.params['window'], 'price_col':self.params['price_col']}}

        precomputed = self.params['use_precomputed_features']
        if not precomputed: self.prices = CircularBuffer(size=self.params['window'])

    def update_state(self, candle_row, open_positions=None):
        precomputed = self.params['use_precomputed_features']
        symbols = self.params['symbols']

        for symbol in symbols:
            if precomputed:
                self.state[symbol]['zscore'] = candle_row[f'{symbol}_zscore']
            else:
                price_col = self.params['price_col']
                price = candle_row[f"{symbol}_{price_col}"]
                self.prices.append(price)
                self.state[symbol]['zscore'] = ffs.zscore(self.prices.to_array())

        for sym, position in open_positions.items():
            side = position['side']
            if not side: self.state[sym]['position'] = None

            valid_sides = {'long', 'short'}
            if side in valid_sides:
                self.state[sym]['position'] = side
            else:
                raise ValueError('invalid position')

    def gen_signal(self):
        symbols = self.state['symbols']
        signal_dict = {}

        for symbol in symbols:
            pos = self.state[symbol]['position']
            z = self.state[symbol]['zscore']

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
                    signal = {'side':'long', 'order_type':'market'}
                elif short_entry:
                    signal = {'side':'short', 'order_type':'market'}
                else:
                    signal = {'side': 'hold'}

            elif pos == 'long' and long_exit:
                signal = {'side':'short', 'order_type':'market'}
            elif pos == 'short' and short_exit:
                signal = {'side':'long', 'order_type':'market'}

            else: raise ValueError('Current position not recognized!')

            signal_dict[symbol] = signal

        return signal_dict

    def gen_order(self, signal):
        symbols = self.params['symbols']
        order_dict = {}

        for symbol in symbols:
            if signal['side'] == 'hold': return [None]
            qty = 1

            order_dict[symbol] = {
                'side':signal['side'],
                'qty':qty,
                'order_type':signal['order_type'],
            }

        return order_dict

    def reset(self):
        self.state.clear()