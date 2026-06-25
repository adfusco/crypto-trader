import asyncio
import os
import re
from datetime import datetime, timedelta, timezone

import pandas as pd
import ccxt.async_support as ccxt_async


def get_path_symbol(sym, replacement='_'):
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', replacement, sym).strip()


def csv_path(symbol, timeframe, save_dir):
    """Per-(symbol, timeframe) CSV path, e.g. raw_csvs/ETH_USDT_1d.csv. Keeping the
    timeframe in the filename stops one timeframe silently overwriting — or being
    read as — another."""
    return os.path.join(save_dir, f'{get_path_symbol(symbol)}_{timeframe}.csv')


def date_to_ms(date_str):
    dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def fetch_to_csvs(symbols, timeframe, start, end, path_to_csvs, exchange_id='mexc'):
    """Fetch OHLCV covering [start, end] (date strings; end=None -> now) and write
    per-(symbol, timeframe) CSVs. Owns exchange lifecycle + the event loop."""
    start_ms = date_to_ms(start)
    end_ms = date_to_ms(end) if end else int(datetime.now(timezone.utc).timestamp() * 1000)
    step_ms = get_minutes(timeframe) * 60 * 1000
    limit = max(1, (end_ms - start_ms) // step_ms + 1)

    exchange = getattr(ccxt_async, exchange_id)()

    async def _run():
        try:
            await fetch_symbols_ohlcv(
                exchange=exchange, symbols=symbols, timeframe=timeframe,
                limit=limit, since=start_ms, save_dir=path_to_csvs,
            )
        finally:
            await exchange.close()
    asyncio.run(_run())


def get_minutes(timeframe):
    unit = timeframe[-1]
    unit_minutes = {
        'm': 1,
        'h': 60,
        'd': 1440,
        'w': 10080,
        'M': 43829
    }

    return unit_minutes[unit]

async def fetch_symbol(exchange, symbol, symbol_dataframes, timeframe='1d', limit=500, since=None, save_dir='raw_csvs'):
    os.makedirs(save_dir, exist_ok=True)
    if symbol not in exchange.markets:
        raise ValueError(f"symbol {symbol} not found on {exchange.id}")

    try:
        print(f'fetching {symbol} since {datetime.fromtimestamp(since / 1000, tz=timezone.utc)}...')
        data = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit, since=since)
        print(f"{symbol}: fetched {len(data)} rows")

        if not data:
            # empty window (e.g. `since` predates the listing); signal no progress
            # so the caller skips this window instead of crashing on iloc[-1].
            return None

        new_dataframe = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        new_dataframe['timestamp'] = pd.to_datetime(new_dataframe['timestamp'], unit='ms')

        old_df = symbol_dataframes.get(symbol)
        if old_df is not None:
            new_dataframe = pd.concat([old_df, new_dataframe], ignore_index=True)
        symbol_dataframes[symbol] = new_dataframe

        last_timestamp = new_dataframe.iloc[-1]['timestamp']
        last_timestamp_ms = int(last_timestamp.timestamp() * 1000)
        return last_timestamp_ms

    except Exception as e:
        print(f'error fetching {symbol}: {e}')
        return None


async def fetch_with_delay(exchange, symbol, symbol_dataframes, timeframe, limit, since, save_dir, delay):
    await asyncio.sleep(delay)
    return await fetch_symbol(exchange, symbol, symbol_dataframes, timeframe, limit, since, save_dir)


async def fetch_symbols_ohlcv(exchange, symbols, timeframe='1d', limit=500, since=None, save_dir='raw_csvs'):
    batch_size = 15
    delay_between_batches = 1.0
    delay_between_fetches = 1 / (exchange.rateLimit * 1000 * 1.25)

    # fetch_ohlcv(since=X) is inclusive (returns candles with ts >= X), so the
    # next batch must start one timeframe past the last candle to avoid
    # re-fetching it as a duplicate at each batch boundary.
    step_ms = get_minutes(timeframe) * 60 * 1000

    symbol_dataframes = {}
    symbol_since_timestamps = {}
    for symbol in symbols:
        if since is None:
            minutes = get_minutes(timeframe) * limit
            since = datetime.now() - timedelta(minutes=minutes)
            since = int(since.replace(tzinfo=timezone.utc).timestamp() * 1000)
        symbol_since_timestamps[symbol] = since

    await exchange.load_markets()

    while limit > 0:
        for i in range(0, len(symbols), batch_size):
            symbol_batch = symbols[i:i+batch_size]
            tasks = []

            for j, symbol in enumerate(symbol_batch):
                delay = j*delay_between_fetches
                fetch_delay_params = {
                    'exchange':exchange,
                    'symbol':symbol,
                    'symbol_dataframes':symbol_dataframes,
                    'timeframe':timeframe,
                    'limit':min(limit, 500),
                    'since':symbol_since_timestamps[symbol],
                    'save_dir':save_dir,
                    'delay':delay
                }
                tasks.append(fetch_with_delay(**fetch_delay_params))

            last_timestamps = await asyncio.gather(*tasks)
            for symbol, last_timestamp in zip(symbol_batch, last_timestamps):
                if last_timestamp is not None:
                    symbol_since_timestamps[symbol] = last_timestamp + step_ms
                else:
                    # empty window -> skip ahead by the batch span so a late-listed
                    # symbol can advance toward the range where its data begins
                    symbol_since_timestamps[symbol] += min(limit, 500) * step_ms

            await asyncio.sleep(delay_between_batches)
        limit -= 500

    for symbol, dataframe in symbol_dataframes.items():
        full_path = csv_path(symbol, timeframe, save_dir)
        dataframe.to_csv(full_path, index=False)
        print(f"{symbol}: saved to {full_path}")