#determines how we will attempt to fill the order
class DummyExecutor:
    def __init__(self, portfolio, simulator):
        self.portfolio = portfolio
        self.simulator = simulator

    def execute_order(self, order, candle):
        if order is not None:
            fills = self.simulator.simulate_order(order, candle)

            for fill in fills:
                self.portfolio.update_with_fill(fill)
