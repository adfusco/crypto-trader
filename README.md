# Crypto Trading Backtester (WIP)

This project is an **in-progress framework** for exploring quantitative trading strategies on cryptocurrency data.  
It is not a fully polished library, but it demonstrates the underlying architecture for a backtesting engine with data ingestion, strategy evaluation, and portfolio performance analysis.

## Project Overview
- **Asset Analysis** (`asset_analysis/`)  
  Playground for preprocessing and exploring asset data.  
- **Backtesting Engine** (`backtest/`, `main_backtest.py`)  
  Candle-level simulation engine for testing strategies and tracking portfolios.  
- **Strategies** (`strategies/`)  
  Example trading strategies (e.g., mean reversion) that plug into the backtester.  
- **Metrics** (`metrics/`)  
  Tools for evaluating performance after a backtest.  
- **Data Management** (`data_ingestion/`)  
  Handles raw and cleaned market data for backtests.  
- **Feature Engineering** (`feature_engineering/`)  
  Functions to construct features used by strategies.  
- **Logs** (`logs/`)  
  Stores trade and portfolio logs for backtest runs.  
- **Live Trading Placeholder** (`main_live.py`)  
  Intended for future live execution integration.

## Project Structure
- `asset_analysis/`  
  Asset preprocessing & exploratory analysis
- `backtest/`  
  Backtesting engine and simulation modules
- `data_ingestion/`  
  Raw and cleaned data management
- `feature_engineering/`  
  Feature construction for strategies
- `metrics/`  
  Performance evaluation tools
- `strategies/`  
  Trading strategy implementations
- `logs/`  
  Backtest logs
- `main_backtest.py`  
  Script for running custom backtests
- `main_live.py`  
  Placeholder for live trading
- `requirements.txt`  
  Python dependencies

## Status
- Core backtesting engine implemented
- Example strategies included
- Asset analysis playground in progress
- Live trading integration not implemented

## Example (WIP)
Currently, `main_backtest.py` contains a basic template to manually run a backtest.
Users can modify main_backtest.py to experiment with different strategies and configurations.

## Installation
```bash
git clone https://github.com/adfusco/crypto-trader
cd crypto-trader
pip install -r requirements.txt
```
