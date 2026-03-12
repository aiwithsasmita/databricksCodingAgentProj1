"""
Forecasting Engine
Holt-Winters exponential smoothing, linear trend extrapolation,
confidence bands, and scenario modeling.
"""

import pandas as pd
import numpy as np
from scipy import stats


def holt_winters_forecast(series: pd.Series, periods: int = 6,
                           alpha: float = 0.3, beta: float = 0.1,
                           gamma: float = 0.2, season_len: int = 12) -> dict:
    """
    Multiplicative Holt-Winters exponential smoothing.
    Returns dict with forecast values, confidence bands, and components.
    """
    y = series.values.astype(float)
    n = len(y)

    if n < season_len + 2:
        return _linear_fallback(series, periods)

    # Initialize level, trend, seasonal
    level = np.mean(y[:season_len])
    trend = (np.mean(y[season_len:2*season_len]) - np.mean(y[:season_len])) / season_len \
        if n >= 2 * season_len else (y[-1] - y[0]) / n

    seasonal = np.zeros(season_len)
    for i in range(season_len):
        vals = [y[j] for j in range(i, n, season_len)]
        seasonal[i] = np.mean(vals) / level if level != 0 else 1.0

    # Fit
    fitted = np.zeros(n)
    levels = np.zeros(n)
    trends = np.zeros(n)
    residuals = np.zeros(n)

    for t in range(n):
        s_idx = t % season_len
        if t == 0:
            fitted[t] = (level + trend) * seasonal[s_idx]
        else:
            fitted[t] = (levels[t-1] + trends[t-1]) * seasonal[s_idx]

        prev_level = levels[t-1] if t > 0 else level
        prev_trend = trends[t-1] if t > 0 else trend

        s_val = seasonal[s_idx]
        if s_val == 0:
            s_val = 1.0

        levels[t] = alpha * (y[t] / s_val) + (1 - alpha) * (prev_level + prev_trend)
        trends[t] = beta * (levels[t] - prev_level) + (1 - beta) * prev_trend
        seasonal[s_idx] = gamma * (y[t] / levels[t]) + (1 - gamma) * seasonal[s_idx]
        residuals[t] = y[t] - fitted[t]

    # Forecast
    rmse = np.sqrt(np.mean(residuals[-12:] ** 2))
    forecast_vals = np.zeros(periods)
    lower_80 = np.zeros(periods)
    upper_80 = np.zeros(periods)
    lower_95 = np.zeros(periods)
    upper_95 = np.zeros(periods)

    last_level = levels[-1]
    last_trend = trends[-1]

    for h in range(periods):
        s_idx = (n + h) % season_len
        point = (last_level + (h + 1) * last_trend) * seasonal[s_idx]
        forecast_vals[h] = point

        spread = rmse * np.sqrt(h + 1)
        lower_80[h] = point - 1.28 * spread
        upper_80[h] = point + 1.28 * spread
        lower_95[h] = point - 1.96 * spread
        upper_95[h] = point + 1.96 * spread

    return {
        "forecast": forecast_vals,
        "lower_80": lower_80, "upper_80": upper_80,
        "lower_95": lower_95, "upper_95": upper_95,
        "fitted": fitted,
        "rmse": rmse,
        "last_level": last_level,
        "last_trend": last_trend,
    }


def _linear_fallback(series: pd.Series, periods: int) -> dict:
    """Simple linear trend fallback when not enough data for HW."""
    y = series.values.astype(float)
    x = np.arange(len(y))
    slope, intercept, _, _, se = stats.linregress(x, y)

    forecast_x = np.arange(len(y), len(y) + periods)
    forecast_vals = slope * forecast_x + intercept
    rmse = np.sqrt(np.mean((y - (slope * x + intercept)) ** 2))

    spread = np.array([rmse * np.sqrt(h + 1) for h in range(periods)])
    return {
        "forecast": forecast_vals,
        "lower_80": forecast_vals - 1.28 * spread,
        "upper_80": forecast_vals + 1.28 * spread,
        "lower_95": forecast_vals - 1.96 * spread,
        "upper_95": forecast_vals + 1.96 * spread,
        "fitted": slope * x + intercept,
        "rmse": rmse,
        "last_level": forecast_vals[0],
        "last_trend": slope,
    }


def forecast_total_spend(df: pd.DataFrame, periods: int = 6) -> pd.DataFrame:
    """Forecast total allowed PMPM across all CPTs, states, plans."""
    monthly = df.groupby("month").agg(
        total_allowed=("allowed_amount", "sum"),
        member_months=("member_months", "first"),
    ).reset_index().sort_values("month")
    monthly["pmpm"] = monthly["total_allowed"] / monthly["member_months"]

    hw = holt_winters_forecast(monthly["pmpm"], periods=periods)

    last_date = monthly["month"].max()
    future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1),
                                  periods=periods, freq="MS")

    forecast_df = pd.DataFrame({
        "month": future_dates,
        "pmpm_forecast": hw["forecast"],
        "lower_80": hw["lower_80"],
        "upper_80": hw["upper_80"],
        "lower_95": hw["lower_95"],
        "upper_95": hw["upper_95"],
        "is_forecast": True,
    })

    actual_df = pd.DataFrame({
        "month": monthly["month"],
        "pmpm_actual": monthly["pmpm"],
        "pmpm_fitted": hw["fitted"],
        "is_forecast": False,
    })

    return actual_df, forecast_df, hw["rmse"]


def forecast_by_category(df: pd.DataFrame, periods: int = 6) -> dict:
    """Forecast PMPM by service category."""
    results = {}
    for cat in df["category"].unique():
        cat_df = df[df["category"] == cat]
        monthly = cat_df.groupby("month").agg(
            total_allowed=("allowed_amount", "sum"),
            member_months=("member_months", "first"),
        ).reset_index().sort_values("month")
        monthly["pmpm"] = monthly["total_allowed"] / monthly["member_months"]

        if len(monthly) < 6:
            continue

        hw = holt_winters_forecast(monthly["pmpm"], periods=periods)
        last_date = monthly["month"].max()
        future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1),
                                      periods=periods, freq="MS")

        results[cat] = {
            "actual_months": monthly["month"],
            "actual_pmpm": monthly["pmpm"],
            "fitted": hw["fitted"],
            "forecast_months": future_dates,
            "forecast": hw["forecast"],
            "lower_95": hw["lower_95"],
            "upper_95": hw["upper_95"],
        }
    return results


def scenario_analysis(df: pd.DataFrame, periods: int = 6) -> pd.DataFrame:
    """
    Generate baseline / adverse / favorable scenarios.
    Adverse = baseline + 1 sigma; Favorable = baseline - 1 sigma.
    """
    _, forecast_df, rmse = forecast_total_spend(df, periods)

    forecast_df["scenario_baseline"] = forecast_df["pmpm_forecast"]
    forecast_df["scenario_adverse"] = forecast_df["pmpm_forecast"] + rmse
    forecast_df["scenario_favorable"] = forecast_df["pmpm_forecast"] - rmse

    return forecast_df


def impact_quantification(df: pd.DataFrame, risk_df: pd.DataFrame,
                           top_n: int = 10, months: int = 6) -> pd.DataFrame:
    """
    For top-N risky CPTs, estimate incremental cost over next N months
    if current trend continues.
    """
    top_risks = risk_df.head(top_n).copy()
    impacts = []

    for _, row in top_risks.iterrows():
        cpt = row["cpt_code"]
        sub = df[df["cpt_code"] == cpt].groupby("month")["allowed_amount"].sum()
        sub = sub.sort_index()

        if len(sub) < 6:
            continue

        recent_avg = sub.tail(6).mean()
        baseline_avg = sub.tail(12).head(6).mean() if len(sub) >= 12 else sub.head(6).mean()
        monthly_excess = max(0, recent_avg - baseline_avg)

        impacts.append({
            "cpt_code": cpt,
            "description": row["cpt_description"],
            "category": row["category"],
            "risk_score": row["risk_score"],
            "signal_type": row["signal_type"],
            "monthly_baseline": round(baseline_avg, 0),
            "monthly_current": round(recent_avg, 0),
            "monthly_excess": round(monthly_excess, 0),
            "projected_excess_6m": round(monthly_excess * months, 0),
        })

    return pd.DataFrame(impacts)
