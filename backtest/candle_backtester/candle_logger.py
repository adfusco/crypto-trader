import pandas as pd
import os

class Logger:
    def __init__(self, base_path='logs', flush_point=100):
        self.trade_log = []
        self.portfolio_log = []
        self.base_path = base_path
        self.flush_point = flush_point

    def log_trade(self, trade_dict):
        #add warnings/error raise if dict not properly formatted?
        self.trade_log.append(trade_dict)
        if len(self.trade_log) >= self.flush_point:
            self.flush_trade_log()

    def log_portfolio_update(self, portfolio_dict):
        #add warnings/error raise if dict not properly formatted?
        self.portfolio_log.append(portfolio_dict)
        if len(self.portfolio_log) >= self.flush_point:
            self.flush_portfolio_log()

    def flush_trade_log(self):
        full_path = f'{self.base_path}/trade_log.csv'
        if os.path.exists(self.base_path):
            mode = 'a'
            header = False
        else:
            os.makedirs(self.base_path)
            mode = 'w'
            header = True

        pd.DataFrame(self.trade_log).to_csv(full_path, mode=mode, header=header, index=True)
        self.trade_log = []

    def flush_portfolio_log(self):
        full_path = f'{self.base_path}/portfolio_log.csv'
        if os.path.exists(self.base_path):
            mode = 'a'
            header = False
        else:
            os.makedirs(self.base_path)
            mode = 'w'
            header = True

        pd.DataFrame(self.portfolio_log).to_csv(full_path, mode=mode, header=header, index=True)
        self.portfolio_log = []