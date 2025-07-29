from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split


class ProbabilityCalibrator:
    def __init__(self):
        self.model = LogisticRegression(max_iter=1000)

    def fit(self, X: np.ndarray, y: np.ndarray):
        X = X.reshape(-1, 1)
        self.model.fit(X, y)
        preds = self.model.predict_proba(X)[:, 1]
        auc = roc_auc_score(y, preds)
        print(f"Calibration AUC: {auc:.4f}")
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X = X.reshape(-1, 1)
        return self.model.predict_proba(X)[:, 1]

    def threshold_by_youden(self, X: np.ndarray, y: np.ndarray) -> float:
        from sklearn.metrics import roc_curve

        probs = self.predict_proba(X)
        fpr, tpr, thr = roc_curve(y, probs)
        youden_j = tpr - fpr
        idx = np.argmax(youden_j)
        return thr[idx] 