#determines how we will attempt to fill the order
class DummyExecutor:
    def __init__(self, portfolio, simulator):
        self.portfolio = portfolio
        self.simulator = simulator

    def execute_order(self, order, candle):
        if order is not None:
            fill = self.simulator.simulate_order(order, candle)
            self.portfolio.update_with_fill(fill)
