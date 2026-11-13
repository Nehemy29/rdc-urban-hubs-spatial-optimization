"""Evaluate CatBoost versus a fitted class-speed baseline on held-out corridors."""
import argparse
from pathlib import Path

CLASSES = ("primary_km", "secondary_km", "local_km", "track_km")
FEATURES = (*CLASSES, "unpaved_share", "ferry_count")
REQUIRED = ("trip_id", "corridor_group", "observed_minutes", "source_type", "source_ref", *FEATURES)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observations", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--threshold", type=float, default=120)
    args = parser.parse_args()
    import numpy as np
    import pandas as pd
    from scipy.optimize import nnls
    from sklearn.model_selection import GroupKFold
    d = pd.read_csv(args.observations, dtype={k: str for k in REQUIRED[:2] + REQUIRED[3:5]})
    if missing := set(REQUIRED) - set(d):
        parser.error(f"Missing columns: {sorted(missing)}")
    d = d.loc[:, list(REQUIRED)].copy()
    if d.isna().any().any() or d.empty or d.trip_id.duplicated().any():
        parser.error("Provide complete observations with unique trip IDs.")
    for name in ("trip_id", "corridor_group", "source_ref"):
        if d[name].str.strip().eq("").any():
            parser.error(f"Blank {name}")
    if not d.source_type.isin(["gps_observed", "operator_observed"]).all():
        parser.error("Only independently observed durations are eligible; no router estimates or simulations.")
    groups = d.corridor_group.str.strip()
    if groups.nunique() < 3:
        parser.error("At least three independent corridor groups are required to run this diagnostic.")
    numeric = d[[*FEATURES, "observed_minutes"]].apply(pd.to_numeric)
    if (not np.isfinite(numeric).all().all() or (numeric < 0).any().any()
        or (numeric.observed_minutes <= 0).any() or (numeric.unpaved_share > 1).any()
        or (numeric[list(CLASSES)].sum(axis=1) <= 0).any()
        or (numeric.ferry_count % 1 != 0).any()
        or not np.isfinite(args.threshold) or args.threshold <= 0):
        parser.error("Check positive durations and route lengths, road shares, ferry counts and threshold.")
    from catboost import CatBoostRegressor
    x, y = numeric[list(FEATURES)], numeric.observed_minutes.to_numpy()
    xb = x[[*CLASSES, "ferry_count"]].to_numpy()
    out = d[["trip_id", "corridor_group", "observed_minutes"]].copy()
    for f, (tr, te) in enumerate(GroupKFold(n_splits=min(5, groups.nunique())).split(x, y, groups), 1):
        assert not set(groups.iloc[tr]) & set(groups.iloc[te])
        coef, _ = nnls(xb[tr], y[tr])
        model = CatBoostRegressor(iterations=300, depth=4, learning_rate=.05,
                                  loss_function="MAE", random_seed=6222,
                                  verbose=False, allow_writing_files=False, thread_count=2)
        model.fit(x.iloc[tr], y[tr])
        out.loc[te, "fold"] = f
        out.loc[te, "baseline_minutes"] = np.maximum(0, xb[te] @ coef)
        out.loc[te, "catboost_minutes"] = np.maximum(0, model.predict(x.iloc[te]))
    metrics = []
    for col in ("baseline_minutes", "catboost_minutes"):
        for label, mask in (("all", np.ones(len(y), dtype=bool)),
                            ("near_threshold", abs(y - args.threshold) <= 30)):
            pred, obs = out[col].to_numpy()[mask], y[mask]
            n = len(obs)
            metrics.append(dict(model=col, subset=label, n=n, corridors=groups[mask].nunique(),
                threshold_minutes=args.threshold, mae_minutes=np.mean(abs(pred-obs)) if n else None,
                bias_minutes=np.mean(pred-obs) if n else None,
                false_covered=int(((pred<=args.threshold)&(obs>args.threshold)).sum()),
                false_uncovered=int(((pred>args.threshold)&(obs<=args.threshold)).sum())))
    args.output.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output / "held_out_predictions.csv", index=False)
    pd.DataFrame(metrics).to_csv(args.output / "metrics.csv", index=False)

if __name__ == "__main__":
    main()
