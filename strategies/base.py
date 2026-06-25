class Strategy:
    @classmethod
    def default_params(cls):
        return {}

    def __init__(self, params: dict):
        self.params = {**self.default_params(), **params}
        self.state = {}
        # single-asset features are computed per-symbol pre-merge; multi-asset
        # features (e.g. a spread) are computed on the merged frame post-merge.
        self.required_features = {}
        self.required_multi_features = {}

    def update_state(self, candle_row, open_positions=None):
        # ingest the new bar (and current positions) into self.state
        pass

    def gen_signal(self):
        # generate a trade action from the current state
        pass

    def gen_order(self, signal, row, portfolio):
        pass

    def select_universe(self, train_prices):
        # Walk-forward hook (runs before fit_fold_params): choose which symbols to
        # trade in the upcoming fold from the configured universe, given only the
        # train-window prices. Return a symbol list, or None to sit the fold out.
        # Default: trade the whole configured set (no selection).
        return self.params['symbols']

    def fit_fold_params(self, train_prices):
        # Walk-forward hook: fit any fold-local parameters (e.g. a hedge ratio)
        # on the train-window price frame and return them as param overrides.
        # Default: nothing to fit.
        return {}