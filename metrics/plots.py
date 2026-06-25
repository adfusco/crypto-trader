import matplotlib.pyplot as plt


def _breakeven_cost(x, y):
    """First cost level where a return-like metric crosses zero, linearly
    interpolated between the bracketing points. None if it never goes negative."""
    for i in range(len(y) - 1):
        if y[i] >= 0 >= y[i + 1]:
            if y[i] == y[i + 1]:
                return x[i]
            return x[i] + (x[i + 1] - x[i]) * (y[i] / (y[i] - y[i + 1]))
    return None


def plot_cost_sweep(table, param, metric='total_return'):
    """Plot a swept metric against a transaction-cost parameter, marking the
    break-even cost when the metric is return-like (crosses zero)."""
    x = table[param].values
    y = table[metric].values

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(x, y, marker='o', color='steelblue', label=metric)

    if metric == 'total_return':
        ax.axhline(0, color='gray', linestyle='--', alpha=0.7, label='Break-even')
        breakeven = _breakeven_cost(x, y)
        if breakeven is not None:
            ax.axvline(breakeven, color='red', linestyle=':', alpha=0.8,
                       label=f'Break-even {param} = {breakeven:.4g}')

    ax.set_xlabel(param)
    ax.set_ylabel(metric)
    ax.set_title(f'{metric} vs {param}')
    ax.legend(loc='best')
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def plot_performance(metrics):
    equity = metrics.equity_curve['equity']
    benchmark = metrics.benchmark_curve()
    underwater = metrics.underwater_series()

    fig, (ax_eq, ax_dd) = plt.subplots(
        2, 1, figsize=(12, 8), sharex=True,
        gridspec_kw={'height_ratios': [3, 1]},
    )

    # --- top panel: equity vs. buy-and-hold ---
    ax_eq.plot(equity.index, equity.values, label='Strategy', color='steelblue')
    ax_eq.plot(benchmark.index, benchmark.values, label='Buy & Hold',
               color='gray', linestyle='--', alpha=0.8)

    # shade the max-drawdown window
    peak_ts, trough_ts = metrics.max_drawdown_window()
    ax_eq.axvspan(peak_ts, trough_ts, color='red', alpha=0.08, label='Max drawdown')

    # trade markers at exits: green up = win, red down = loss.
    # exit timestamps can repeat (multi-asset same-bar exits) and so can the
    # equity index, so map through a deduped lookup to get one y per trade.
    eq_lookup = equity[~equity.index.duplicated(keep='first')]
    trades = metrics.trade_history
    wins = trades.index[trades['pnl'] > 0]
    losses = trades.index[trades['pnl'] <= 0]
    ax_eq.scatter(wins, eq_lookup.reindex(wins).values, marker='^', color='green',
                  s=40, zorder=3, label='Winning exit')
    ax_eq.scatter(losses, eq_lookup.reindex(losses).values, marker='v', color='red',
                  s=40, zorder=3, label='Losing exit')

    ax_eq.set_ylabel('Equity')
    ax_eq.set_title('Strategy vs. Buy & Hold')
    ax_eq.legend(loc='best')
    ax_eq.grid(alpha=0.3)

    # --- bottom panel: underwater (drawdown) ---
    ax_dd.fill_between(underwater.index, underwater.values, 0,
                       color='red', alpha=0.3)
    ax_dd.set_ylabel('Drawdown')
    ax_dd.set_xlabel('Date')
    ax_dd.grid(alpha=0.3)

    fig.tight_layout()
    return fig
