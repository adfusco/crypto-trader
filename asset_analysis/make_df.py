import ccxt


def get_top_syms(number, by='quoteVolume'):
    """Return the top-`number` USDT spot symbols on MEXC ranked by `by` (e.g.
    quoteVolume), as a list of (symbol, value) tuples."""
    exchange = ccxt.mexc()
    exchange.load_markets()
    tickers = exchange.fetch_tickers()

    usdt = {}
    for symbol, ticker in tickers.items():
        if '/USDT' in symbol and ticker[by] and ticker[by] > 0:
            usdt[symbol] = ticker[by]

    by_volume = sorted(usdt.items(), key=lambda x: x[1], reverse=True)
    return by_volume[:number]
