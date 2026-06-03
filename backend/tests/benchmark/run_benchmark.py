#!/usr/bin/env python3
"""
批量评估提取精度 MAPE / RMSE。
用法: python tests/benchmark/run_benchmark.py --dir tests/benchmark/line_charts
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def evaluate(pred_csv: Path, truth_csv: Path) -> dict:
    pred = pd.read_csv(pred_csv)
    truth = pd.read_csv(truth_csv)
    if "x" not in pred.columns or "y" not in pred.columns:
        return {"error": "missing columns"}
    merged = pd.merge_asof(
        pred.sort_values("x"),
        truth.sort_values("x"),
        on="x",
        suffixes=("_pred", "_truth"),
    )
    err = np.abs(
        (merged.y_truth - merged.y_pred) / merged.y_truth.replace(0, np.nan)
    )
    mape = float(err.mean() * 100) if len(err) else float("nan")
    rmse = float(np.sqrt(((merged.y_truth - merged.y_pred) ** 2).mean()))
    return {"MAPE": mape, "RMSE": rmse, "n": len(merged)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, required=True)
    args = parser.parse_args()
    results = []
    for truth in sorted(args.dir.glob("*_truth.csv")):
        stem = truth.name.replace("_truth.csv", "")
        pred = args.dir / f"{stem}_pred.csv"
        if not pred.exists():
            continue
        m = evaluate(pred, truth)
        m["chart"] = stem
        results.append(m)
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
