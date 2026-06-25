import argparse
import os
import pickle

import matplotlib.pyplot as plt

from metrics.metrics import Metrics
from metrics.plots import plot_performance

HERE = os.path.dirname(os.path.abspath(__file__))


def load_metrics(portfolio_name):
    portfolio_path = os.path.join(HERE, 'portfolio_data', f'{portfolio_name}.pkl')
    with open(portfolio_path, 'rb') as f:
        portfolio_data = pickle.load(f)
    return Metrics(portfolio_data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Print stats and plot a backtest result.')
    parser.add_argument('portfolio_name', nargs='?', default='mr_basic_backtest',
                        help='config name (PKL stem in portfolio_data/)')
    args = parser.parse_args()

    metrics = load_metrics(args.portfolio_name)
    metrics.print_stats()

    plot_performance(metrics)
    plt.show()
