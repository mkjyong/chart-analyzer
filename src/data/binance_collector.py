from __future__ import annotations

import datetime as dt
import logging
from typing import List, Literal, Optional

import pandas as pd
from binance.client import Client
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


Interval = Literal[
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "8h",
    "12h",
    "1d",
]


class BinanceDataClient:
    """간단한 Binance 선물 데이터 수집기.

    Notes
    -----
    - USDT-M 선물 전용.
    - REST 엔드포인트로 히스토리 캔들 가져오기.
    - 가져온 데이터는 pandas.DataFrame(UTC 인덱스) 반환.
    """

    def __init__(
        self,
        api_key: Optional[str] | None = None,
        api_secret: Optional[str] | None = None,
        testnet: bool = False,
    ) -> None:
        api_key = api_key or os.getenv("BINANCE_API_KEY")
        api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        self.client = Client(api_key, api_secret, testnet=testnet)
        # Futures (UM) endpoint
        self.client.FUTURES_URL = "https://fapi.binance.com/fapi"

    def fetch_klines(
        self,
        symbol: str,
        interval: Interval,
        start: str | dt.datetime,
        end: str | dt.datetime | None = None,
        limit: int = 1500,
    ) -> pd.DataFrame:
        """주어진 구간의 캔들 OHLCV를 DataFrame 으로 반환.

        Parameters
        ----------
        symbol : str
            예: 'BTCUSDT'
        interval : Interval
        start : str or datetime
            "2023-01-01" 형식 혹은 datetime
        end : str or datetime, optional
        limit : int
            한번의 요청에 가져올 최대 캔들 수 (<=1500)
        """
        start_ts = (
            int(pd.Timestamp(start).timestamp() * 1000)
            if not isinstance(start, (int, float))
            else int(start)
        )
        end_ts: Optional[int]
        if end is not None:
            end_ts = (
                int(pd.Timestamp(end).timestamp() * 1000)
                if not isinstance(end, (int, float))
                else int(end)
            )
        else:
            end_ts = None
        raw = self.client.futures_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str=start_ts,
            end_str=end_ts,
            limit=limit,
        )
        if not raw:
            raise ValueError("No klines returned from Binance")
        df = self._klines_to_df(raw)
        return df

    @staticmethod
    def _klines_to_df(raw: List[list]) -> pd.DataFrame:
        cols = [
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "num_trades",
            "taker_base_volume",
            "taker_quote_volume",
            "ignore",
        ]
        df = pd.DataFrame(raw, columns=cols)
        df[cols[1:]] = df[cols[1:]].apply(pd.to_numeric, errors="coerce")
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        df.set_index("open_time", inplace=True)
        return df


if __name__ == "__main__":
    client = BinanceDataClient(testnet=False)
    btc = client.fetch_klines("BTCUSDT", "1h", "2024-01-01", "2024-02-01")
    print(btc.head()) 