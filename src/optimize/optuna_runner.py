from __future__ import annotations

import argparse
import datetime as dt
import gc
import os
from typing import Dict

import optuna
import pandas as pd

from data.binance_collector import BinanceDataClient
from backtest.engine import run_backtest
from backtest.strategy import MultiIndicatorStrategy
from optimize.param_space import suggest_params


def objective(trial: optuna.Trial, df: pd.DataFrame) -> float:
    params = suggest_params(trial)

    cerebro = run_backtest(
        df=df,
        strategy_cls=MultiIndicatorStrategy,
        commission=0.005,
        leverage=10,
        **params,
    )
    final_value = cerebro.broker.getvalue()
    # maximize final portfolio value
    return final_value


def run_optimization(
    symbol: str,
    interval: str,
    start: str,
    end: str,
    trials: int = 100,
    study_name: str | None = None,
    storage: str | None = None,
):
    client = BinanceDataClient()
    df = client.fetch_klines(symbol.upper(), interval, start, end)
    df = df[["open", "high", "low", "close", "volume"]]

    study = optuna.create_study(
        direction="maximize",
        study_name=study_name,
        storage=storage,
        load_if_exists=bool(storage),
    )
    study.optimize(lambda t: objective(t, df), n_trials=trials)
    print("Best value:", study.best_value)
    print("Best params:", study.best_params)
    return study


def main():
    parser = argparse.ArgumentParser(description="Optuna optimization for multi-indicator strategy")
    parser.add_argument("symbol", type=str)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--trials", type=int, default=50)
    parser.add_argument("--storage", type=str, help="Optuna storage URL (e.g., sqlite:///study.db)")
    parser.add_argument("--name", type=str, help="Study name")
    args = parser.parse_args()

    run_optimization(
        symbol=args.symbol,
        interval=args.interval,
        start=args.start,
        end=args.end,
        trials=args.trials,
        study_name=args.name,
        storage=args.storage,
    )


if __name__ == "__main__":
    main() 