import ccxt
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import os
import re

def clean_symbol(sym, replacement='_'):
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', replacement, sym).strip()

def fetch_data(symbols, timeframe='1m', limit=500, save_dir='data'):
    os.makedirs(save_dir, exist_ok=True)
    exchange = ccxt.mexc()

    for symbol in symbols:
        data = exchange.fetch_ohlcv(symbol, timeframe, limit)

        candle_df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        candle_df['timestamp'] = pd.to_datetime(candle_df['timestamp'], unit='ms')

        symbol_name = clean_symbol(symbol) + '_' + str(timeframe) + '.csv'
        candle_df.to_csv(os.path.join(save_dir, symbol_name), index=False)

if True:
    symbols=['BTC/USDT', 'ETC/USDT', 'SOL/USDT']