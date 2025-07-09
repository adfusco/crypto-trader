from backtest.candle_backtester.candle_executor import execute_order
from feature_engineering.rolling_features import add_rolling_features

def run_backtest(strategy, candle_df, use_precomputed_features, start_index=0, end_index=None):
    if end_index is None: end_index = len(candle_df)
    candle_df = candle_df[(candle_df['timestamp'] >= start_index) & (candle_df['timestamp'] <= end_index)].copy()

    if use_precomputed_features:
        required_features = strategy.params['required_features']
        candle_df = add_rolling_features(candle_df, required_features)

    for i in range(0, len(candle_df)):
        row = candle_df.iloc[i]

        strategy.update_state(row)
        signal = strategy.gen_signal()
        order = strategy.gen_order(signal)

        execute_order(order)
