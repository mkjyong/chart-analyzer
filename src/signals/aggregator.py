from __future__ import annotations

from typing import Dict, List
import numpy as np


class SignalAggregator:
    """가중합 방식으로 다중 지표·타임프레임 점수를 합산."""

    def __init__(self, weights: Dict[str, float]):
        """
        Parameters
        ----------
        weights : dict
            key: signal 이름 (임의)
            value: weight (합계 1.0 권장)
        """
        self.weights = weights

    def score(self, signals: Dict[str, int | float]) -> float:
        """weights x signals 을 곱해 총합."""
        total = 0.0
        for k, v in self.weights.items():
            total += v * signals.get(k, 0)
        return total

    def classify(self, signals: Dict[str, int | float], threshold: float = 0.0) -> int:
        """score>threshold 양수면 long, 음수면 short, 아니면 neutral."""
        s = self.score(signals)
        if s > threshold:
            return 1
        elif s < -threshold:
            return -1
        return 0 