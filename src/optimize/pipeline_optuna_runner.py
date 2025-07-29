from __future__ import annotations

import argparse

import optuna

from pipeline.backtest_pipeline import BacktestPipeline


INTERVALS = ["5m", "15m", "1h"]  # can be parameterized


def objective(trial: optuna.Trial, symbol: str, start: str, end: str):
    # suggest weights
    weights = {}
    for iv in INTERVALS:
        weights[iv] = trial.suggest_float(f"w_{iv}", 0.0, 1.0)
    # normalize
    total_w = sum(weights.values())
    weights = {f"sig_{iv}": w / total_w for iv, w in weights.items()}

    prob_threshold = trial.suggest_float("prob_threshold", 0.6, 0.95)

    pipe = BacktestPipeline(
        symbol=symbol,
        intervals=INTERVALS,
        start=start,
        end=end,
        aggregator_weights=weights,
        prob_threshold=prob_threshold,
    )
    cerebro = pipe.execute()
    final_value = cerebro.broker.getvalue()
    return final_value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--trials", type=int, default=50)
    parser.add_argument("--storage")
    parser.add_argument("--study")
    args = parser.parse_args()

    study = optuna.create_study(
        direction="maximize",
        study_name=args.study,
        storage=args.storage,
        load_if_exists=bool(args.storage),
    )
    study.optimize(lambda t: objective(t, args.symbol, args.start, args.end), n_trials=args.trials)
    print("Best value", study.best_value)
    print("Best params", study.best_params)


if __name__ == "__main__":
    main() 