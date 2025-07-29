from __future__ import annotations

import optuna


def suggest_params(trial: optuna.Trial) -> dict:
    """RSI, Supertrend, SL/RR parameter space."""
    params = {
        # RSI
        "rsi_period": trial.suggest_int("rsi_period", 2, 6),
        "rsi_overbought": trial.suggest_int("rsi_overbought", 70, 90),
        "rsi_oversold": trial.suggest_int("rsi_oversold", 10, 40),
        # Supertrend
        "st_atr_period": trial.suggest_int("st_atr_period", 7, 21),
        "st_multiplier": trial.suggest_float("st_multiplier", 1.0, 5.0, step=0.1),
        # Risk params
        "sl_pct": trial.suggest_float("sl_pct", 0.003, 0.01, step=0.0005),
        "rr": trial.suggest_float("rr", 1.2, 3.0, step=0.1),
    }
    return params 