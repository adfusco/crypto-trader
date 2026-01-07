#determines how we will attempt to execute the order

# The dummy executor simply places all orders at once
class DummyExecutor:
    def __init__(self, portfolio, simulator):
        self.portfolio = portfolio
        self.simulator = simulator

    def execute_orders(self, orders, candle):
        if orders is not None:
            fills = self.simulator.simulate_orders(orders, candle)

            for fill in fills:
                self.portfolio.update_with_fill(fill)
