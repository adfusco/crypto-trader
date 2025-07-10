class Strategy:
    @staticmethod
    def required_params():
        return []

    @classmethod
    def default_params(cls):
        return {}

    def __init__(self, params: dict):
        self.params = {**self.default_params(), **params}
        self.state = {}

    def update_state(self, market_candle):
        #ingests relevant data from new candle
        pass

    def gen_signal(self):
        #generates trade action given current state
        pass

    def gen_order(self, signal):
        #produces info for real order given signal and portfolio information
        pass

    def reset(self):
        self.state.clear()