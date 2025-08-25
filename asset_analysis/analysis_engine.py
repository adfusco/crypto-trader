from asset_analysis.make_df import get_top_syms, get_merged_df

import pandas as pd
from datetime import datetime
from itertools import combinations

from statsmodels.tsa.vector_ar.vecm import coint_johansen
from arch.unitroot import PhillipsPerron

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


def johansen_test_pairs(price_df, det_order=1, lag_num=1):
    results = []
    for pair in combinations(price_df.columns, r=2):
        sub_df = price_df[list(pair)].dropna()

        result = coint_johansen(sub_df, det_order, lag_num)
        if result.lr1[0] > result.cvt[0, 1]:
            results.append({
                "pair":pair,
                "trace_stat":result.lr1[0],
                "crit_val_5pct":result.cvt[0, 1],
                "hedge_ratio":result.evec[:, 0]
            })

    results = pd.DataFrame(results)
    results.sort_values(by='trace_stat', ascending=False, inplace=True)
    return results


def main():
    #TEMPORARY SOLUTION...
    saved = True

    num_symbols = 30
    by = 'quoteVolume'
    price_col = 'close'

    base_path = '../data_ingestion/clean_data/asset_analysis/'
    csv_name = f'top_{num_symbols}_{by}_{datetime.now().date()}.csv'
    full_path = base_path + csv_name

    if not saved:
        symbols_by_vol = get_top_syms(num_symbols, by)
        symbols = [symbol for symbol, volume in symbols_by_vol]

        merge_params = {
            'symbols':symbols,
            'timeframe':'1d',
            'limit':500,
            'output_path':full_path
        }
        get_merged_df(**merge_params)


    merged_df = pd.read_csv(full_path)
    clean_df = merged_df.drop(columns=[x for x in merged_df.columns if price_col not in x])
    clean_df = clean_df.drop(columns=[x for x in clean_df.columns if pd.isna(clean_df.iloc[0][x])])

    valid_df = clean_df
    crit_value = 0.1
    drop = []
    for col in valid_df.columns:
        pp_test = PhillipsPerron(valid_df[col])
        if pp_test.pvalue < crit_value:
            drop.append(col)
    valid_df = valid_df.drop(columns=drop)

    print(johansen_test_pairs(valid_df))

if __name__ == '__main__':
    main()