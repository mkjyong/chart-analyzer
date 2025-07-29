import argparse
import datetime as dt

import pandas as pd

from data.binance_collector import BinanceDataClient
from backtest.engine import run_backtest
from backtest.strategy import MultiIndicatorStrategy


def main():
    parser = argparse.ArgumentParser(description="Backtest multi-indicator strategy on Binance futures")
    parser.add_argument("symbol", type=str, help="Trading pair, e.g., BTCUSDT")
    parser.add_argument("--start", type=str, required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", type=str, required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--interval", type=str, default="1h", help="Kline interval, default 1h")
    args = parser.parse_args()

    client = BinanceDataClient()
    df = client.fetch_klines(args.symbol.upper(), args.interval, args.start, args.end)

    # Keep only necessary columns
    df = df[["open", "high", "low", "close", "volume"]]

    cerebro = run_backtest(df, MultiIndicatorStrategy)
    cerebro.plot()


if __name__ == "__main__":
    main() 