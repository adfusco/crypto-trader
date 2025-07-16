import numpy as np
import pandas as pd
from datetime import datetime

class Metrics:
    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.timestamps = portfolio.timestamps

        self.equity_curve = pd.DataFrame(portfolio.equity_curve)
        self.equity_curve['timestamp'] = pd.to_datetime(self.equity_curve['timestamp'])
        self.equity_curve.set_index('timestamp', inplace=True)

        self.max_equity = portfolio.max_equity
        self.drawdowns = portfolio.drawdowns
        self.max_drawdown_amt = portfolio.max_drawdown_amt
        self.max_drawdown_pct = portfolio.max_drawdown_pct

        self.trade_history = pd.DataFrame(portfolio.trade_history)
        self.trade_history['exit_timestamp'] = pd.to_datetime(self.trade_history['exit_timestamp'])
        self.trade_history.set_index('exit_timestamp', inplace=True)


    def compute_stats(self, start=None, end=None):
        start = start or self.portfolio.timestamps[0]
        end = end or self.portfolio.timestamps[-1]

        return {
            'total_return':self.total_return(start, end),
            'cagr':self.cagr(start, end),
            'sharpe_ratio':self.sharpe_ratio(start, end),
            'profit_factor':self.profit_factor(start, end),
            'win_rate':self.win_rate(start, end),
            'avg_trade_return':self.avg_trade_return(start, end),
            'avg_holding_time':self.avg_holding_time(start, end)
        }

    def return_basic_stats(self):
        return {
            'max_equity':self.max_equity,
            'num_drawdowns':len(self.drawdowns),
            'max_drawdown_amt':self.max_drawdown_amt,
            'max_drawdown_pct':self.max_drawdown_pct,
            'num_trades':len(self.trade_history)
        }

    def total_return(self, start, end):
        sliced = self.equity_curve.loc[start:end]
        start_eq = sliced['equity'].iloc[0]
        end_eq = sliced['equity'].iloc[-1]
        return (end_eq - start_eq) / start_eq

    def _time_elapsed(self, start_ts, end_ts):
        start = pd.to_datetime(start_ts)
        end = pd.to_datetime(end_ts)
        return end-start

    def cagr(self, start, end):
        delta = self._time_elapsed(start, end)
        years = delta.total_seconds() / (365.25 * 24 * 60 * 60)

        sliced = self.equity_curve.loc[start:end]
        start_eq = sliced['equity'].iloc[0]
        end_eq = sliced['equity'].iloc[-1]

        return (end_eq / start_eq) ** (1/years) - 1

    def _risk_free_curve(self, start, end, rf_rate=0.05, compounding='daily'):
        dates = self.equity_curve.loc[start:end].index
        n_days = (dates - dates[0]).days.values

        if compounding == 'daily': rf_returns = (1 + rf_rate) ** n_days - 1
        else: rf_returns = np.exp(rf_rate * n_days)
        return pd.Series(rf_returns, index=dates)

    def _excess_returns(self, start, end, rf_rate, compounding):
        sliced = self.equity_curve.loc[start:end]
        equities = sliced['equity'].values
        base_equity = sliced['equity'].iloc[0]

        returns = (equities - base_equity) / base_equity
        risk_free_returns = self._risk_free_curve(start, end, rf_rate, compounding)
        return returns - risk_free_returns

    def sharpe_ratio(self, start, end, obv_per_year=365, rf_rate=0.05, compounding='daily'):
        excess_free_returns = self._excess_returns(start, end, rf_rate, compounding)
        mean = np.mean(excess_free_returns)
        std = np.std(excess_free_returns)

        return mean/std * np.sqrt(obv_per_year)

    def profit_factor(self, start, end):
        sliced = self.trade_history.loc[start:end]

        gross_profit = sum(sliced['pnl'].iloc[i] for i in range(len(sliced)) if sliced['pnl'].iloc[i] > 0)
        gross_loss = sum(abs(sliced['pnl'].iloc[i]) for i in range(len(sliced)) if sliced['pnl'].iloc[i] < 0)

        if gross_loss == 0:
            return float('inf')
        return gross_profit / gross_loss

    def win_rate(self, start, end):
        sliced = self.trade_history.loc[start:end]
        return (sliced['pnl'] > 0).mean()

    def avg_trade_return(self, start, end):
        sliced = self.trade_history.loc[start:end]
        return ((sliced['exit_price'] - sliced['entry_price'])/sliced['entry_price'] + 1).mean()

    def avg_holding_time(self, start, end):
        sliced = self.trade_history.loc[start:end]
        return (sliced.index - sliced['entry_timestamp']).mean()