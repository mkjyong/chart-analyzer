from __future__ import annotations

import pandas as pd
import numpy as np
from indicators.rsi import compute_rsi
from indicators.supertrend import compute_supertrend


def generate_signals(
    df: pd.DataFrame,
    rsi_period: int = 3,
    rsi_overbought: int = 80,
    rsi_oversold: int = 20,
    st_atr_period: int = 10,
    st_multiplier: float = 3.0,
) -> pd.DataFrame:
    """RSI + Supertrend 기반 진입 시그널(+1/-1/0).

    Parameters
    ----------
    df : DataFrame
        OHLC dataframe with ['open','high','low','close']
    Returns
    -------
    DataFrame
        with column 'signal' (+1 long, -1 short, 0 none)
    """
    out = df.copy().reset_index(drop=False)
    out["rsi"] = compute_rsi(out["close"], length=rsi_period)
    st = compute_supertrend(out[["open", "high", "low", "close"]], length=st_atr_period, multiplier=st_multiplier)
    out["supertrend_dir"] = st["SUPERTd_{}_{}_{}_".format(st_atr_period, st_multiplier, st_atr_period)].values if isinstance(st, pd.DataFrame) else st["SUPERTd_10_3.0_10"].values
    # Compute signals
    conditions_long = (out["rsi"] < rsi_oversold) & (out["supertrend_dir"] == 1)
    conditions_short = (out["rsi"] > rsi_overbought) & (out["supertrend_dir"] == -1)
    out["signal"] = 0
    out.loc[conditions_long, "signal"] = 1
    out.loc[conditions_short, "signal"] = -1
    return out.set_index(df.index) 