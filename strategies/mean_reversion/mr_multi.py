from strategies.base import Strategy
from backtest.utils.circular_buffer import CircularBuffer
import feature_engineering.feature_functions as ffs

class MeanReversionMulti(Strategy):
    @classmethod
    def default_params(cls):
        return {
            'use_precomputed_features': True,
            'symbols': None,
            'window': 20,
            'price_col': 'close',
            'risk_pct': 0.02,
            'zscores': {'long_entry': -1, 'long_exit': -1, 'short_entry': 1, 'short_exit': 1}
        }

    def __init__(self, params: dict):
        super().__init__(params)
        self.required_features = {'zscore': {'window': self.params['window'], 'price_col': self.params['price_col']}}

        symbols = self.params['symbols'] or []
        for symbol in symbols:
            self.state[symbol] = {'zscore': None, 'position': None}

        precomputed = self.params['use_precomputed_features']
        if not precomputed:
            self.prices = {sym: CircularBuffer(size=self.params['window']) for sym in symbols}

    def update_state(self, candle_row, open_positions=None):
        precomputed = self.params['use_precomputed_features']
        symbols = self.params['symbols']

        for symbol in symbols:
            if precomputed:
                self.state[symbol]['zscore'] = candle_row[f'{symbol}_zscore']
            else:
                price_col = self.params['price_col']
                price = candle_row[f"{symbol}_{price_col}"]
                self.prices[symbol].append(price)
                self.state[symbol]['zscore'] = ffs.zscore(self.prices[symbol].to_array())

            self.state[symbol]['position'] = (open_positions or {}).get(symbol, {}).get('side', None)

    def gen_signal(self):
        symbols = self.params['symbols']
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
                    signal = {'side': 'long', 'order_type': 'market'}
                elif short_entry:
                    signal = {'side': 'short', 'order_type': 'market'}
                else:
                    signal = {'side': 'hold'}
            elif pos == 'long' and long_exit:
                signal = {'side': 'short', 'order_type': 'market'}
            elif pos == 'short' and short_exit:
                signal = {'side': 'long', 'order_type': 'market'}
            else:
                signal = {'side': 'hold'}

            signal_dict[symbol] = signal

        return signal_dict

    def gen_order(self, signal_dict, row, portfolio):
        order_dict = {}
        equity = portfolio.get_equity()
        risk_pct = self.params['risk_pct']
        price_col = self.params['price_col']

        for symbol, signal in signal_dict.items():
            if signal['side'] == 'hold':
                continue
            price = row[f'{symbol}_{price_col}']
            qty = int(equity * risk_pct / price)
            if qty == 0:
                continue
            order_dict[symbol] = {
                'side': signal['side'],
                'qty': qty,
                'order_type': signal['order_type'],
            }

        return order_dict