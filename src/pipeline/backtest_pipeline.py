from __future__ import annotations

from typing import List, Dict

import pandas as pd
import numpy as np

from data.multi_tf_loader import MultiTFDataLoader
from signals.rsi_supertrend import generate_signals
from signals.aggregator import SignalAggregator
from probability.calibrator import ProbabilityCalibrator
from backtest.engine import run_backtest
from backtest.strategy import MultiIndicatorStrategy


class BacktestPipeline:
    def __init__(
        self,
        symbol: str,
        intervals: List[str],
        start: str,
        end: str,
        aggregator_weights: Dict[str, float] | None = None,
        prob_threshold: float = 0.8,
    ):
        self.symbol = symbol
        self.intervals = intervals
        self.start = start
        self.end = end
        self.loader = MultiTFDataLoader()
        self.weights = aggregator_weights or {f"sig_{iv}": 1 / len(intervals) for iv in intervals}
        self.aggregator = SignalAggregator(self.weights)
        self.prob_threshold = prob_threshold
        self.calibrator = ProbabilityCalibrator()

    def prepare_data(self) -> pd.DataFrame:
        df = self.loader.fetch_and_merge(self.symbol, self.intervals, self.start, self.end)
        return df

    def compute_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        sig_cols = {}
        for iv in self.intervals:
            ohlc = df[[f"open_{iv}", f"high_{iv}", f"low_{iv}", f"close_{iv}"]].copy()
            ohlc.columns = ["open", "high", "low", "close"]
            sig_df = generate_signals(ohlc)
            df[f"sig_{iv}"] = sig_df["signal"].values
            sig_cols[f"sig_{iv}"] = f"sig_{iv}"
        # total score
        df["score"] = df.apply(lambda row: self.aggregator.score(row[sig_cols.values()].to_dict()), axis=1)
        return df

    def calibrate(self, df: pd.DataFrame):
        # Define label: profit positive? For calibration we approximate using future return of close_ base interval
        base_iv = min(self.intervals, key=self.loader._interval_minutes)
        future_ret = df[f"close_{base_iv}"].pct_change().shift(-1)  # 1 step ahead
        y = (future_ret > 0).astype(int).values
        X = df["score"].values
        mask = ~np.isnan(X) & ~np.isnan(y)
        self.calibrator.fit(X[mask], y[mask])
        thr = self.calibrator.threshold_by_youden(X[mask], y[mask])
        self.prob_threshold = max(thr, self.prob_threshold)
        print(f"Calibrated probability threshold: {self.prob_threshold:.3f}")

    def run_backtest(self, df: pd.DataFrame):
        # Convert score -> probability -> trade_signal
        prob = self.calibrator.predict_proba(df["score"].values)
        df["trade_signal"] = 0
        df.loc[prob >= self.prob_threshold, "trade_signal"] = 1
        df.loc[prob <= 1 - self.prob_threshold, "trade_signal"] = -1

        base_iv = min(self.intervals, key=self.loader._interval_minutes)
        feed_df = df[[
            f"open_{base_iv}",
            f"high_{base_iv}",
            f"low_{base_iv}",
            f"close_{base_iv}",
            f"volume_{base_iv}",
            "trade_signal",
        ]].copy()
        feed_df.columns = ["open", "high", "low", "close", "volume", "signal"]

        from backtest.signal_strategy import SignalTradeStrategy

        cerebro = run_backtest(feed_df, SignalTradeStrategy)
        return cerebro

    def execute(self):
        df = self.prepare_data()
        df = self.compute_signals(df)
        self.calibrate(df)
        cerebro = self.run_backtest(df)
        return cerebro 