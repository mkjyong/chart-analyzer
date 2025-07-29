from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import optuna

from pipeline.backtest_pipeline import BacktestPipeline
from optimize.pipeline_optuna_runner import INTERVALS, objective


def parse_args():
    p = argparse.ArgumentParser("Full pipeline runner")
    p.add_argument("symbol", help="Trading symbol, e.g., BTCUSDT")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--opt_trials", type=int, default=0, help="If >0, run Optuna optimization first")
    p.add_argument("--storage", help="Optuna storage URI")
    p.add_argument("--study", help="Study name")
    p.add_argument("--report", help="Path to save JSON report")
    return p.parse_args()


def run_optuna(symbol: str, start: str, end: str, trials: int, storage: str | None, study_name: str | None):
    study = optuna.create_study(direction="maximize", study_name=study_name, storage=storage, load_if_exists=bool(storage))
    study.optimize(lambda t: objective(t, symbol, start, end), n_trials=trials)
    return study


def main():
    args = parse_args()

    # Step 1: Optimization (optional)
    weights = None
    prob_threshold = 0.8
    if args.opt_trials > 0:
        study = run_optuna(args.symbol, args.start, args.end, args.opt_trials, args.storage, args.study)
        best = study.best_params
        prob_threshold = best.pop("prob_threshold")
        weights = {k.replace("w_", "sig_"): v for k, v in best.items() if k.startswith("w_")}
        total = sum(weights.values())
        weights = {k: v / total for k, v in weights.items()}
    else:
        weights = {f"sig_{iv}": 1 / len(INTERVALS) for iv in INTERVALS}

    # Step 2: Run Backtest with best params
    pipe = BacktestPipeline(
        symbol=args.symbol,
        intervals=INTERVALS,
        start=args.start,
        end=args.end,
        aggregator_weights=weights,
        prob_threshold=prob_threshold,
    )
    cerebro = pipe.execute()
    final_value = cerebro.broker.getvalue()
    print(f"Final portfolio value: {final_value:.2f}")

    # Optional report
    if args.report:
        report_path = Path(args.report)
        report_path.write_text(json.dumps({
            "symbol": args.symbol,
            "start": args.start,
            "end": args.end,
            "final_value": final_value,
            "weights": weights,
            "prob_threshold": prob_threshold,
        }, indent=2))
        print(f"Report saved to {report_path}")


if __name__ == "__main__":
    sys.exit(main()) 