import matplotlib.pyplot as plt
import pickle

from metrics.candle_metrics import Metrics

portfolio_name = 'MeanReversionBasic'
portfolio_path = 'portfolio_data/' + portfolio_name + '.pkl'

with open(portfolio_path, 'rb') as f:
    portfolio_data = pickle.load(f)

metrics = Metrics(portfolio_data)
metrics.print_stats()

plt.plot(metrics.equity_curve.index, metrics.equity_curve['equity'])
plt.show()