from strategies.base import Strategy
from backtest.utils.circular_buffer import CircularBuffer
import feature_engineering.feature_functions as ffs

class MeanReversionBasic(Strategy):
    def __init__(self, params: dict):
        super().__init__(params)
        self.prices = CircularBuffer(self.params['window'])

    def update_state(self, price, position=None):
        self.prices.append(price)
        self.state['zscore'] = ffs.compute_newest_zscore(self.params['window'], self.prices.to_array())

        valid_positions = {'long', 'short', 'hold'}
        if position:
            if position in valid_positions:
                self.state['position'] = position
            else:
                raise ValueError('invalid position')

    def gen_signal(self):
        pos = self.state.get('position')
        z = self.state['zscore']

        z_long_entry = self.state['long_entry_zscore']
        z_long_exit = self.state['long_exit_zscore']
        z_short_entry = self.state['short_entry_zscore']
        z_short_exit = self.state['short_exit_zscore']

        long_entry = z < z_long_entry
        long_exit = z > z_long_exit
        short_entry = z > z_short_entry
        short_exit = z < z_short_exit

        if pos is None:
            if long_entry:
                return {'side':'buy', 'order_type':'market'}
            elif short_entry:
                return {'side':'sell', 'order_type':'market'}

        elif pos == 'long' and long_exit:
            return {'side':'sell', 'order_type':'market'}
        elif pos == 'short' and short_exit:
            return {'side':'buy', 'order_type':'market'}

        return {'side':'hold'}

    def gen_order(self, signal):
        if signal['side'] == 'hold': return None

        return {
            'side':signal['side'],
            'order_type':signal['order_type'],
            'asset':self.state['asset'],
            'quantity':self.state['qty']
        }

    def reset(self):
        self.state.clear()