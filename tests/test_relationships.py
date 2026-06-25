import numpy as np
import pandas as pd
import pytest

from asset_analysis.relationships import (
    RELATIONSHIP_REGISTRY, ols_estimator, correlation_screen,
)


def test_registry_exposes_expected_capabilities():
    reg = RELATIONSHIP_REGISTRY
    assert set(reg) >= {'johansen', 'correlation', 'ols'}
    # johansen does both; correlation screens only; ols estimates only
    assert reg['johansen'].screen and reg['johansen'].estimate
    assert reg['correlation'].screen and reg['correlation'].estimate is None
    assert reg['ols'].estimate and reg['ols'].screen is None


def test_require_helpers_raise_on_missing_capability():
    with pytest.raises(ValueError):
        RELATIONSHIP_REGISTRY['correlation'].require_estimate()
    with pytest.raises(ValueError):
        RELATIONSHIP_REGISTRY['ols'].require_screen()


def test_ols_estimator_recovers_known_beta():
    # A = 3*B + noise-free -> beta ~ 3
    b = np.linspace(1, 100, 300)
    df = pd.DataFrame({'A': 3.0 * b, 'B': b})
    beta, meta = ols_estimator(df)
    assert abs(beta - 3.0) < 1e-6
    assert 'resid_std' in meta


def test_correlation_screen_ranks_perfectly_correlated_pair_first():
    n = 300
    base = np.cumsum(np.random.default_rng(0).normal(size=n))
    df = pd.DataFrame({
        'A': base,
        'B': base * 2.0,          # identical returns -> corr 1
        'C': np.cumsum(np.random.default_rng(1).normal(size=n)),
    })
    table = correlation_screen(df, min_obs=50)
    assert table.iloc[0]['pair'] == ('A', 'B')
    assert abs(table.iloc[0]['correlation'] - 1.0) < 1e-6
