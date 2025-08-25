import feature_engineering.feature_functions as ffs
import numpy as np
import pandas as pd

#single asset functions
def zscore(df, price_col, window=20):
    price_series = df[price_col]

    mean = price_series.rolling(window).mean()
    std = price_series.rolling(window).std()

    return {'zscore': (price_series - mean)/std}


#multi asset functions
def pairs_spread(df, hedge_ratio, symbols, price_col):
    sym_a, sym_b = symbols

    price_series_a = df[f'{sym_a}_{price_col}']
    price_series_b = df[f'{sym_b}_{price_col}']

    return {f'{sym_a}_{sym_b} pairs spread': price_series_a - hedge_ratio * price_series_b}


'''
    df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=window).rsi()
    df['stoch'] = ta.momentum.StochasticOscillator(high=df['high'], low=df['low'], close=df['close'], window=window).stoch()

    df['sma_20'] = ta.trend.SMAIndicator(close=df['close'], window=20).sma_indicator()
    df['ema_20'] = ta.trend.EMAIndicator(close=df['close'], window=20).ema_indicator()
    df['macd'] = ta.trend.MACD(close=df['close']).macd_diff()

    df['atr'] = ta.volatility.AverageTrueRange(high=df['high'], low=df['low'], close=df['close']).average_true_range()
    df['bollinger_high'] = ta.volatility.BollingerBands(close=df['close']).bollinger_hband()
    df['bollinger_low'] = ta.volatility.BollingerBands(close=df['close']).bollinger_lband()

    df['obv'] = ta.volume.OnBalanceVolumeIndicator(close=df['close'], volume=df['volume']).on_balance_volume()
'''