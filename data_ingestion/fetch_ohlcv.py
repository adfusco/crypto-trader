import pandas as pd
import asyncio
import os
import re
import random

def clean_symbol(sym, replacement='_'):
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', replacement, sym).strip()


async def fetch_symbol(exchange, symbol, timeframe='1m', limit=500, save_dir='data'):
    os.makedirs(save_dir, exist_ok=True)

    try:
        print(f'fetching {symbol}...')
        data = await exchange.fetch_ohlcv(symbol, timeframe, limit)

        candle_df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        candle_df['timestamp'] = pd.to_datetime(candle_df['timestamp'], unit='ms')

        symbol_name = clean_symbol(symbol) + '_' + str(timeframe) + '.csv'
        candle_df.to_csv(os.path.join(save_dir, symbol_name), index=False)

    except Exception as e:
        print(f'error fetching {symbol}: {e}')
        return None


async def fetch_with_delay(exchange, symbol, timeframe, limit, save_dir, delay=1.0):
    await asyncio.sleep(delay)
    return await fetch_symbol(exchange, symbol, timeframe, limit, save_dir)


async def fetch_symbols_ohlcv(exchange, symbols, timeframe='1m', limit=500, save_dir='data'):
    batch_size = 15
    delay_between_batches = 1.0

    for i in range(0, len(symbols), batch_size):
        symbol_batch = symbols[i:i + batch_size]
        tasks = []
        for j, symbol in enumerate(symbol_batch):
            tasks.append(asyncio.create_task(fetch_with_delay(exchange, symbol, timeframe, limit, save_dir, delay=j*random.uniform(0.05, 0.1))))

        await asyncio.gather(*tasks)
        await asyncio.sleep(delay_between_batches)

    await exchange.close()