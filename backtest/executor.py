# Routes orders through the simulator and applies the resulting fills to the
# portfolio. This implementation submits every order in the batch at once.
class DummyExecutor:
    def __init__(self, portfolio, simulator):
        self.portfolio = portfolio
        self.simulator = simulator

    def execute_orders(self, orders, candle):
        if orders is not None:
            fills = self.simulator.simulate_orders(orders, candle)

            for fill in fills:
                self.portfolio.update_with_fill(fill)
