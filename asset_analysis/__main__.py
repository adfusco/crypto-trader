"""Screening CLI: python -m asset_analysis <symbols...> [--method ...]

Ranks the candidate pairs in a symbol universe by a relationship method, matching
the `python -m backtest <config>` workflow. Methods come from RELATIONSHIP_REGISTRY,
so adding one makes it available here automatically.
"""
import argparse
import os

from asset_analysis.analysis_engine import screen_pairs
from asset_analysis.relationships import RELATIONSHIP_REGISTRY
from data_ingestion.fetch_ohlcv import fetch_to_csvs, csv_path


def main():
    parser = argparse.ArgumentParser(prog='asset_analysis',
                                     description='Screen symbol pairs for a relationship.')
    screen_methods = [name for name, rel in RELATIONSHIP_REGISTRY.items() if rel.screen]
    parser.add_argument('symbols', nargs='+', help='symbols, e.g. BTC/USDT ETH/USDT DOT/USDT')
    parser.add_argument('--method', default='johansen', choices=screen_methods,
                        help='relationship/screening method')
    parser.add_argument('--path', default='data_ingestion/raw_csvs', help='raw CSV directory')
    parser.add_argument('--fetch', action='store_true', help='fetch fresh OHLCV before screening')
    parser.add_argument('--timeframe', default='1d')
    parser.add_argument('--start', default='2019-01-01',
                        help='screen window start (also the fetch start with --fetch)')
    parser.add_argument('--end', default=None,
                        help='screen window end (default: latest)')
    parser.add_argument('--top', type=int, default=20, help='rows to print (0 = all)')
    parser.add_argument('--save', metavar='PATH', help='write the full ranked table to a CSV')
    args = parser.parse_args()

    if args.fetch:
        fetch_to_csvs(args.symbols, args.timeframe, args.start, args.end, args.path)

    present = [s for s in args.symbols
               if os.path.exists(csv_path(s, args.timeframe, args.path))]
    missing = [s for s in args.symbols if s not in present]
    if missing:
        print(f'skipping (no {args.timeframe} CSV; use --fetch): {missing}')
    if not present:
        print(f'no cached {args.timeframe} data for any requested symbol; run with --fetch')
        return

    table = screen_pairs(present, args.path, method=args.method, timeframe=args.timeframe,
                         start=args.start, end=args.end)
    if not len(table):
        print('no pairs found')
        return

    # symbols that survived loading but appear in no ranked pair (dropped by a
    # method's pre-filter, e.g. Phillips-Perron stationarity, or too little overlap)
    ranked = {s for pair in table['pair'] for s in pair}
    excluded = [s for s in present if s not in ranked]
    if excluded:
        print(f'excluded (stationary / insufficient overlap): {excluded}')

    if args.save:
        table.to_csv(args.save, index=False)
        print(f'saved {len(table)} rows to {args.save}')

    shown = table.head(args.top) if args.top > 0 else table
    print(f'\nshowing {len(shown)} of {len(table)} pairs:')
    print(shown.to_string(index=False))


if __name__ == '__main__':
    main()
