from __future__ import annotations

import datetime as dt
from typing import Type

import backtrader as bt
import pandas as pd


class PandasData_bt(bt.feeds.PandasData):
    params = (
        ("datetime", None),
        ("open", "open"),
        ("high", "high"),
        ("low", "low"),
        ("close", "close"),
        ("volume", "volume"),
        ("signal", -1),  # optional
    )

    lines = ("signal",)


def run_backtest(
    df: pd.DataFrame,
    strategy_cls: Type[bt.Strategy],
    cash: float = 100_000.0,
    commission: float = 0.005,  # 0.5% per trade (both sides combined)
    leverage: float = 10.0,
    **strategy_params,
):
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(cash)
    cerebro.broker.setcommission(commission=commission)
    cerebro.broker.set_slippage_perc(perc=0.0)  # no slippage
    cerebro.addsizer(bt.sizers.PercentSizer, perc=100)  # full notional (will be leveraged)

    datafeed = PandasData_bt(dataname=df)
    cerebro.adddata(datafeed)
    cerebro.addstrategy(strategy_cls, **strategy_params)

    print(f"Starting Portfolio Value: {cerebro.broker.getvalue():.2f}")
    cerebro.run()
    print(f"Final Portfolio Value: {cerebro.broker.getvalue():.2f}")
    return cerebro 