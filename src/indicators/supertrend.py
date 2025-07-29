import pandas as pd
import pandas_ta as ta


def compute_supertrend(
    df: pd.DataFrame,
    length: int = 10,
    multiplier: float = 3.0,
) -> pd.DataFrame:
    """Supertrend 값과 방향을 계산.

    Parameters
    ----------
    df : pd.DataFrame
        OHLC 데이터프레임(열: open, high, low, close)
    length : int
        ATR 기간
    multiplier : float
        ATR 곱
    Returns
    -------
    pd.DataFrame
        columns=["ST", "ST_dir"] (Supertrend 값, 추세(1:-1))
    """
    st = ta.supertrend(high=df["high"], low=df["low"], close=df["close"], length=length, multiplier=multiplier)
    return st 