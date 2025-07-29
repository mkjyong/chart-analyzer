from __future__ import annotations

import pandas as pd
from typing import List, Dict

from .binance_collector import BinanceDataClient


class MultiTFDataLoader:
    """여러 타임프레임의 캔들을 하나의 DataFrame으로 병합.

    Notes
    -----
    - 최저(가장 짧은) 타임프레임을 기준으로 리샘플/조인
    - 컬럼 이름 규칙: <col>_<interval>, 예) close_1h, close_4h
    """

    def __init__(self, client: BinanceDataClient | None = None):
        self.client = client or BinanceDataClient()

    def fetch_and_merge(
        self,
        symbol: str,
        intervals: List[str],
        start: str,
        end: str,
    ) -> pd.DataFrame:
        dfs: Dict[str, pd.DataFrame] = {}
        for iv in intervals:
            df = self.client.fetch_klines(symbol, iv, start, end)
            dfs[iv] = df[["open", "high", "low", "close", "volume"]].copy()
            dfs[iv].columns = [f"{c}_{iv}" for c in dfs[iv].columns]

        # 가장 짧은 interval로 정렬
        base_iv = min(intervals, key=self._interval_minutes)
        base_df = dfs.pop(base_iv)

        for iv, df in dfs.items():
            base_df = base_df.join(df, how="left")

        # 결측 보간(앞으로 채우기)
        base_df.fillna(method="ffill", inplace=True)
        return base_df

    @staticmethod
    def _interval_minutes(iv: str) -> int:
        mapping = {
            "1m": 1,
            "3m": 3,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "2h": 120,
            "4h": 240,
            "6h": 360,
            "8h": 480,
            "12h": 720,
            "1d": 1440,
        }
        return mapping[iv] 