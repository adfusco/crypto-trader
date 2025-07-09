import feature_engineering.feature_functions as ffs
import numpy as np
import pandas as pd
import ta.momentum, ta.trend, ta.volatility, ta.volume

def zscore_rolling(df, price_col, window=20):
    price_series = df[price_col]

    mean = price_series.rolling(window).mean()
    std = price_series.rolling(window).std()

    return (price_series.iloc[-1] - mean)/std


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