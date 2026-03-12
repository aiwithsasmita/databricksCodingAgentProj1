"""
Early Warning Signal Engine
Z-score anomaly, CUSUM shift detection, trend acceleration, composite risk scoring.
"""

import pandas as pd
import numpy as np


def zscore_flags(series: pd.Series, window: int = 12, threshold: float = 2.0) -> pd.Series:
    """Flag periods where value exceeds trailing-window z-score threshold."""
    rolling_mean = series.rolling(window, min_periods=6).mean()
    rolling_std = series.rolling(window, min_periods=6).std()
    z = (series - rolling_mean) / rolling_std.clip(lower=1e-9)
    return z.fillna(0), (z.abs() > threshold).fillna(False)


def cusum(series: pd.Series, drift: float = 0.5) -> pd.Series:
    """
    Cumulative sum control chart.
    Detects sustained upward shifts.  drift = slack parameter.
    """
    target = series.iloc[:12].mean() if len(series) >= 12 else series.mean()
    std = series.iloc[:12].std() if len(series) >= 12 else series.std()
    if std == 0 or np.isnan(std):
        return pd.Series(0, index=series.index)

    k = drift * std
    cusum_pos = pd.Series(0.0, index=series.index)

    prev = 0.0
    for i in range(len(series)):
        val = max(0, prev + (series.iloc[i] - target) - k)
        cusum_pos.iloc[i] = val
        prev = val

    return cusum_pos


def trend_acceleration(series: pd.Series, short_window: int = 3,
                        long_window: int = 12) -> tuple[float, float, bool]:
    """
    Compare recent slope (short window) vs trailing slope (long window).
    Returns (short_slope, long_slope, is_accelerating).
    """
    if len(series) < long_window:
        return 0.0, 0.0, False

    y_long = series.iloc[-long_window:].values
    x_long = np.arange(long_window)
    if np.std(y_long) == 0:
        return 0.0, 0.0, False
    long_slope = np.polyfit(x_long, y_long, 1)[0]

    y_short = series.iloc[-short_window:].values
    x_short = np.arange(short_window)
    short_slope = np.polyfit(x_short, y_short, 1)[0]

    is_accel = (short_slope > 0) and (short_slope > long_slope * 1.5)
    return float(short_slope), float(long_slope), bool(is_accel)


def compute_risk_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute composite risk score (0-100) for each CPT × State × Plan combination
    based on the most recent 12 months of data.

    Components:
      - cost_accel   (40%): trend acceleration on allowed PMPM
      - util_accel   (25%): trend acceleration on utilization/1000
      - benchmark_dev (20%): unit cost vs CMS national benchmark
      - intensity     (15%): RVU drift (higher = more complex codes being used)

    Returns a DataFrame with one row per (cpt_code, state, plan_type) + risk details.
    """
    groups = df.groupby(["cpt_code", "state", "plan_type"])
    results = []

    for (cpt, state, plan), gdf in groups:
        gdf = gdf.sort_values("month")
        if len(gdf) < 6:
            continue

        # -- Cost acceleration --
        pmpm_series = gdf["pmpm"]
        short_s, long_s, accel = trend_acceleration(pmpm_series)
        if long_s != 0:
            cost_ratio = abs(short_s / long_s)
        else:
            cost_ratio = abs(short_s) * 10
        cost_score = min(100, cost_ratio * 25) if short_s > 0 else 0

        # -- Utilization acceleration --
        util_series = gdf["utilization_per_1000"]
        short_u, long_u, util_accel = trend_acceleration(util_series)
        if long_u != 0:
            util_ratio = abs(short_u / long_u)
        else:
            util_ratio = abs(short_u) * 10
        util_score = min(100, util_ratio * 25) if short_u > 0 else 0

        # -- Benchmark deviation --
        benchmark = gdf["national_benchmark"].iloc[-1]
        current_uc = gdf["unit_cost"].iloc[-1]
        if benchmark > 0:
            dev_pct = (current_uc / benchmark - 1) * 100
            bench_score = min(100, max(0, dev_pct * 2))
        else:
            bench_score = 0

        # -- Intensity drift (RVU trend) --
        rvu_series = gdf["rvu_total"]
        if rvu_series.std() > 0:
            rvu_z, _ = zscore_flags(rvu_series, window=12, threshold=1.5)
            intensity_score = min(100, abs(rvu_z.iloc[-1]) * 30)
        else:
            intensity_score = 0

        composite = (
            cost_score * 0.40 +
            util_score * 0.25 +
            bench_score * 0.20 +
            intensity_score * 0.15
        )
        composite = round(min(100, max(0, composite)), 1)

        # -- Z-score flag on PMPM --
        _, pmpm_flagged = zscore_flags(pmpm_series)
        is_zscore_flagged = bool(pmpm_flagged.iloc[-1]) if len(pmpm_flagged) > 0 else False

        # -- CUSUM --
        cusum_val = cusum(pmpm_series)
        cusum_current = round(float(cusum_val.iloc[-1]), 2) if len(cusum_val) > 0 else 0

        # -- Signal type --
        signals = []
        if accel:
            signals.append("Cost Accelerating")
        if util_accel:
            signals.append("Utilization Accelerating")
        if is_zscore_flagged:
            signals.append("Z-Score Anomaly")
        if cusum_current > cusum_val.quantile(0.90):
            signals.append("CUSUM Shift")

        results.append({
            "cpt_code": cpt,
            "cpt_description": gdf["cpt_description"].iloc[-1],
            "category": gdf["category"].iloc[-1],
            "subcategory": gdf["subcategory"].iloc[-1],
            "state": state,
            "plan_type": plan,
            "risk_score": composite,
            "cost_accel_score": round(cost_score, 1),
            "util_accel_score": round(util_score, 1),
            "benchmark_score": round(bench_score, 1),
            "intensity_score": round(intensity_score, 1),
            "is_accelerating": accel or util_accel,
            "is_zscore_flagged": is_zscore_flagged,
            "cusum_value": cusum_current,
            "signal_type": "; ".join(signals) if signals else "Normal",
            "current_pmpm": round(float(gdf["pmpm"].iloc[-1]), 4),
            "current_util": round(float(gdf["utilization_per_1000"].iloc[-1]), 4),
            "current_unit_cost": round(float(gdf["unit_cost"].iloc[-1]), 2),
            "short_slope": round(short_s, 6),
            "long_slope": round(long_s, 6),
        })

    result_df = pd.DataFrame(results)
    return result_df.sort_values("risk_score", ascending=False).reset_index(drop=True)


def get_cusum_series(df: pd.DataFrame, cpt_code: str,
                      state: str = None, plan_type: str = None) -> pd.DataFrame:
    """Get CUSUM time series for a specific CPT (optionally filtered by state/plan)."""
    mask = df["cpt_code"] == cpt_code
    if state:
        mask &= df["state"] == state
    if plan_type:
        mask &= df["plan_type"] == plan_type

    sub = df[mask].groupby("month").agg(
        pmpm=("pmpm", "mean"),
        utilization_per_1000=("utilization_per_1000", "mean"),
        unit_cost=("unit_cost", "mean"),
    ).reset_index().sort_values("month")

    if len(sub) < 3:
        return sub

    sub["cusum_pmpm"] = cusum(sub["pmpm"])
    sub["cusum_util"] = cusum(sub["utilization_per_1000"])
    _, sub["zscore_flag"] = zscore_flags(sub["pmpm"])
    return sub
