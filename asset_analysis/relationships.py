"""Pluggable asset-relationship methods.

Each relationship is a `Relationship` bundling up to two capabilities:

  screen(price_df_wide, **params) -> DataFrame[pair, stat, ...]
      ranks every pair in a universe (consumed by screen_pairs / the CLI)
  estimate(price_df_2col) -> (hedge_ratio, meta)
      the tradeable parameter for ONE pair (consumed by a strategy's fit_fold_params)

A method may provide either or both (e.g. 'correlation' is screen-only, 'ols' is
estimate-only). New relationships drop into RELATIONSHIP_REGISTRY as one entry,
keeping a method's screener and estimator defined and named together.
"""
from dataclasses import dataclass
from itertools import combinations
from typing import Callable, Optional

import numpy as np
import pandas as pd
from statsmodels.tsa.vector_ar.vecm import coint_johansen
from arch.unitroot import PhillipsPerron


@dataclass(frozen=True)
class Relationship:
    name: str
    screen: Optional[Callable] = None
    estimate: Optional[Callable] = None

    def require_screen(self):
        if self.screen is None:
            raise ValueError(f"relationship '{self.name}' does not support screening")
        return self.screen

    def require_estimate(self):
        if self.estimate is None:
            raise ValueError(f"relationship '{self.name}' has no estimator")
        return self.estimate


# ----- estimators: tradeable parameter for a single pair -----

def johansen_estimator(price_df, det_order=0, lag_num=1):
    """Hedge ratio beta for the spread A - beta*B from the first Johansen
    cointegrating vector (normalised so A's weight is 1)."""
    price_df = price_df.dropna()
    result = coint_johansen(price_df.values, det_order, lag_num)
    w_a, w_b = result.evec[:, 0]
    meta = {'cointegrated': bool(result.lr1[0] > result.cvt[0, 1]),
            'trace_stat': float(result.lr1[0])}
    return -w_b / w_a, meta


def ols_estimator(price_df, **_):
    """Hedge ratio beta from a static OLS regression A ~ beta*B."""
    price_df = price_df.dropna()
    a = price_df.iloc[:, 0].values
    b = price_df.iloc[:, 1].values
    beta = float(np.polyfit(b, a, 1)[0])
    return beta, {'resid_std': float((a - beta * b).std())}


# ----- screeners: rank candidate pairs in a universe -----

def johansen_screen(price_df, pp_crit=0.1, det_order=0, lag_num=1, min_obs=250):
    """Rank EVERY testable pair by Johansen cointegration trace statistic (not just
    the ones that pass), with a `cointegrated` flag (trace > 5% critical value), so
    near-misses are visible. First drops individually stationary series
    (Phillips-Perron), since cointegration needs I(1) inputs.

    Columns: [pair, trace_stat, crit_5pct, cointegrated, hedge_ratio]."""
    keep = []
    for col in price_df.columns:
        series = price_df[col].dropna()
        if len(series) >= min_obs and PhillipsPerron(series).pvalue >= pp_crit:
            keep.append(col)

    rows = []
    for a, b in combinations(keep, 2):
        sub = price_df[[a, b]].dropna()
        if len(sub) < min_obs:
            continue
        result = coint_johansen(sub.values, det_order, lag_num)
        trace, crit = float(result.lr1[0]), float(result.cvt[0, 1])
        w_a, w_b = result.evec[:, 0]
        rows.append({'pair': (a, b), 'trace_stat': trace, 'crit_5pct': crit,
                     'cointegrated': trace > crit, 'hedge_ratio': -w_b / w_a})

    cols = ['pair', 'trace_stat', 'crit_5pct', 'cointegrated', 'hedge_ratio']
    return pd.DataFrame(rows, columns=cols).sort_values('trace_stat', ascending=False).reset_index(drop=True)


def correlation_screen(price_df, min_obs=250, **_):
    """Rank pairs by correlation of daily returns (discovery only — no tradeable
    parameter). Returns columns [pair, correlation]."""
    returns = price_df.pct_change(fill_method=None)
    rows = []
    for a, b in combinations(price_df.columns, 2):
        sub = returns[[a, b]].dropna()
        if len(sub) < min_obs:
            continue
        rows.append({'pair': (a, b), 'correlation': float(sub[a].corr(sub[b]))})

    cols = ['pair', 'correlation']
    return pd.DataFrame(rows, columns=cols).sort_values('correlation', ascending=False).reset_index(drop=True)


RELATIONSHIP_REGISTRY = {
    'johansen': Relationship('johansen', screen=johansen_screen, estimate=johansen_estimator),
    'correlation': Relationship('correlation', screen=correlation_screen),
    'ols': Relationship('ols', estimate=ols_estimator),
}
