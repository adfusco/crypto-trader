import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import ccxt.async_support as ccxt_async
import ccxt
import asyncio

from data_ingestion.fetch_ohlcv import fetch_symbols_ohlcv
from data_ingestion.prepare_data import prepare_candle_data

def get_top_syms(number, by='quoteVolume'):
    temp_ex = ccxt.mexc()
    temp_ex.load_markets()
    tickers = temp_ex.fetch_tickers()

    market_volumes = []
    for symbol, ticker in tickers.items():
        if ticker[by] and ticker[by] > 0:
            market_volumes.append((symbol, ticker[by]))

    usdt = {}
    for symbol, volume in market_volumes:
        if '/USDT' in symbol:
            usdt[symbol] = volume

    usdt_by_volume = sorted(usdt.items(), key=lambda x: x[1], reverse=True)
    top_n = usdt_by_volume[:number]

    return top_n


def get_merged_df(symbols, timeframe, limit, output_path):
    exchange = ccxt_async.mexc()
    symbols = symbols
    since_ms = None
    path_to_csvs = '../data_ingestion/raw_csvs'

    fetch_params = {
        'exchange':exchange,
        'symbols':symbols,
        'timeframe':timeframe,
        'limit':limit,
        'since':since_ms,
        'save_dir':path_to_csvs
    }

    async def main():
        try: await fetch_symbols_ohlcv(**fetch_params)
        finally: await exchange.close()
    asyncio.run(main())


    cleaning_params = {
        'symbols':symbols,
        'use_precomputed_features':False,
        'features':None,
        'path_to_csvs':path_to_csvs,
        'path_to_output_csv':output_path,
        'merge_on':'timestamp'
    }

    prepare_candle_data(**cleaning_params)