import pandas as pd
import asyncio
import os
import re

def get_path_symbol(sym, replacement='_'):
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', replacement, sym).strip()


async def fetch_symbol(exchange, symbol, timeframe='1m', limit=500, save_dir='data'):
    os.makedirs(save_dir, exist_ok=True)
    if symbol not in exchange.markets:
        raise ValueError(f"symbol {symbol} not found on {exchange.id}")

    try:
        print(f'fetching {symbol}...')
        data = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        print(f"{symbol}: fetched {len(data)} rows")

        candle_df = pd.DataFrame(data, columns=['timestamp', f'open', f'high', f'low', f'close', f'volume'])
        candle_df['timestamp'] = pd.to_datetime(candle_df['timestamp'], unit='ms')

        symbol_name = get_path_symbol(symbol) + '.csv'
        candle_df.to_csv(os.path.join(save_dir, symbol_name), index=False)

    except Exception as e:
        print(f'error fetching {symbol}: {e}')
        return None


async def fetch_with_delay(exchange, symbol, timeframe, limit, save_dir, delay):
    await asyncio.sleep(delay)
    await fetch_symbol(exchange, symbol, timeframe, limit, save_dir)


async def fetch_symbols_ohlcv(exchange, symbols, timeframe='1m', limit=500, save_dir='data'):
    batch_size = 15
    delay_between_batches = 1.0
    delay_between_fetches = exchange.rateLimit * 1.25

    await exchange.load_markets()
    for i in range(0, len(symbols), batch_size):
        symbol_batch = symbols[i:i+batch_size]
        tasks = []
        for j, symbol in enumerate(symbol_batch):
            delay = j*delay_between_fetches
            tasks.append(fetch_with_delay(exchange, symbol, timeframe, limit, save_dir, delay))
        await asyncio.gather(*tasks)
        await asyncio.sleep(delay_between_batches)