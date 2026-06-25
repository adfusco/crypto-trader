from strategies.base import Strategy
from backtest.utils.circular_buffer import CircularBuffer
import feature_engineering.feature_functions as ffs


class PairsMeanReversion(Strategy):
    """Mean-reversion on a cointegration spread (price_A - beta * price_B).

    A single z-score of the spread drives a single hedged decision:
      - long spread = long A, short B (entered when the spread is cheap)
      - short spread = short A, long B (entered when the spread is rich)
    Exits flatten both legs when the spread reverts toward its mean.
    """

    @classmethod
    def default_params(cls):
        return {
            'use_precomputed_features': True,
            'symbols': None,
            'hedge_ratio': 1.0,
            'relationship': 'johansen',  # estimator used to (re)fit the hedge ratio
            'selection': None,  # screener for walk-forward pair pick; None = use 'relationship'
            'window': 20,
            'price_col': 'close',
            'risk_pct': 0.02,
            'zscores': {'long_entry': -1, 'long_exit': 0, 'short_entry': 1, 'short_exit': 0},
        }

    def __init__(self, params: dict):
        super().__init__(params)
        self.required_multi_features = {
            'spread_zscore': {
                'hedge_ratio': self.params['hedge_ratio'],
                'symbols': self.params['symbols'],
                'price_col': self.params['price_col'],
                'window': self.params['window'],
            }
        }
        self.state = {'zscore': None, 'position': None}

        precomputed = self.params['use_precomputed_features']
        if not precomputed:
            self.spread_prices = CircularBuffer(size=self.params['window'])

    def update_state(self, candle_row, open_positions=None):
        precomputed = self.params['use_precomputed_features']
        sym_a, sym_b = self.params['symbols']

        if precomputed:
            self.state['zscore'] = candle_row['spread_zscore']
        else:
            price_col = self.params['price_col']
            beta = self.params['hedge_ratio']
            spread = candle_row[f'{sym_a}_{price_col}'] - beta * candle_row[f'{sym_b}_{price_col}']
            self.spread_prices.append(spread)
            self.state['zscore'] = ffs.zscore(self.spread_prices.to_array())

        # the spread direction is determined by leg A: long A = long spread
        a_side = (open_positions or {}).get(sym_a, {}).get('side', None)
        if a_side == 'long':
            self.state['position'] = 'long_spread'
        elif a_side == 'short':
            self.state['position'] = 'short_spread'
        else:
            self.state['position'] = None

    def gen_signal(self):
        pos = self.state['position']
        z = self.state['zscore']

        z_long_entry = self.params['zscores']['long_entry']
        z_long_exit = self.params['zscores']['long_exit']
        z_short_entry = self.params['zscores']['short_entry']
        z_short_exit = self.params['zscores']['short_exit']

        if pos is None:
            if z < z_long_entry:
                return {'side': 'long_spread', 'order_type': 'market'}
            elif z > z_short_entry:
                return {'side': 'short_spread', 'order_type': 'market'}
        elif pos == 'long_spread' and z > z_long_exit:
            return {'side': 'exit', 'order_type': 'market'}
        elif pos == 'short_spread' and z < z_short_exit:
            return {'side': 'exit', 'order_type': 'market'}

        return {'side': 'hold'}

    def gen_order(self, signal, row, portfolio):
        order_dict = {}
        side = signal['side']
        if side == 'hold':
            return order_dict

        sym_a, sym_b = self.params['symbols']
        order_type = signal['order_type']

        if side == 'exit':
            # flatten both legs at their held quantities
            for symbol in (sym_a, sym_b):
                pos = portfolio.get_position(symbol)
                if pos:
                    reverse = 'long' if pos['side'] == 'short' else 'short'
                    order_dict[symbol] = {
                        'side': reverse,
                        'qty': abs(pos['qty']),
                        'order_type': order_type,
                    }
            return order_dict

        # entries: size leg A from equity, leg B by the hedge ratio
        equity = portfolio.get_equity()
        risk_pct = self.params['risk_pct']
        price_col = self.params['price_col']
        beta = self.params['hedge_ratio']

        price_a = row[f'{sym_a}_{price_col}']
        qty_a = int(equity * risk_pct / price_a)
        qty_b = int(qty_a * abs(beta))
        if qty_a == 0 or qty_b == 0:
            return order_dict

        # spread = A - beta*B. To go long the spread, long A; the B leg's side
        # depends on beta's sign (short B when beta > 0, long B when beta < 0)
        if side == 'long_spread':
            a_side = 'long'
            b_side = 'short' if beta > 0 else 'long'
        else:  # short_spread
            a_side = 'short'
            b_side = 'long' if beta > 0 else 'short'

        order_dict[sym_a] = {'side': a_side, 'qty': qty_a, 'order_type': order_type}
        order_dict[sym_b] = {'side': b_side, 'qty': qty_b, 'order_type': order_type}
        return order_dict

    def select_universe(self, train_prices):
        # Pick the pair to trade this fold by screening the configured universe on
        # the train window only (never the test window). With <=2 symbols there's
        # no choice to make, so trade them directly (fixed-pair behavior). With a
        # larger universe, screen and take the top-ranked cointegrated pair, or
        # return None to sit the fold out if nothing cointegrates.
        from asset_analysis.relationships import RELATIONSHIP_REGISTRY
        universe = self.params['symbols']
        if len(universe) <= 2:
            return universe

        price_col = self.params['price_col']
        price_df = train_prices[[f'{s}_{price_col}' for s in universe]].copy()
        price_df.columns = universe

        method = self.params.get('selection') or self.params['relationship']
        table = RELATIONSHIP_REGISTRY[method].require_screen()(price_df)
        cointegrated = table[table['cointegrated']]
        if cointegrated.empty:
            return None
        return list(cointegrated.iloc[0]['pair'])  # table is sorted best-first

    def fit_fold_params(self, train_prices):
        # Re-estimate the hedge ratio on the train window so beta never sees the
        # test data (closes the in-sample leak from a full-sample beta).
        # The estimator is pluggable via the 'relationship' param.
        from asset_analysis.relationships import RELATIONSHIP_REGISTRY
        sym_a, sym_b = self.params['symbols']
        price_col = self.params['price_col']
        pair_prices = train_prices[[f'{sym_a}_{price_col}', f'{sym_b}_{price_col}']]
        estimator = RELATIONSHIP_REGISTRY[self.params['relationship']].require_estimate()
        beta, _ = estimator(pair_prices)
        return {'hedge_ratio': beta}
