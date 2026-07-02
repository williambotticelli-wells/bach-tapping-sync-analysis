#!/usr/bin/env python3
"""First-pass exploratory hypotheses for beta-sync Bach tapping analyses.

These tests are deliberately conservative in interpretation: time bins overlap
and observations are nested within tracks/pieces. Outputs include raw,
within-track centered, and within-piece centered correlations to distinguish
global track differences from local time-varying relationships.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


BACH_ROOT = Path(__file__).resolve().parents[1]
IN_TABLE = (
    BACH_ROOT
    / "analysis"
    / "beta_sync_multimodal"
    / "bach_time_binned_multimodal_with_matlab_toolboxes.csv"
)
OUT_DIR = BACH_ROOT / "analysis" / "beta_sync_hypotheses"
OUT_DIR.mkdir(parents=True, exist_ok=True)


TARGETS = [
    "istc_mean_max_unique_per_sec",
]

FEATURE_GROUPS = {
    "acoustic_energy_salience": [
        "rms_mean",
        "onset_strength_mean",
        "mir_rms",
        "mir_lowenergy",
    ],
    "timbre_spectrum": [
        "spectral_centroid_hz_mean",
        "spectral_bandwidth_hz_mean",
        "spectral_rolloff_hz_mean",
        "zero_crossing_rate_mean",
        "mir_brightness",
        "mir_roughness",
        "mir_centroid",
    ],
    "symbolic_density_complexity": [
        "n_note_onsets",
        "active_note_count",
        "approx_polyphony",
        "cv_midi_ioi",
        "mtb_n_note_onsets",
        "mtb_active_note_count",
        "mtb_approx_polyphony",
        "mtb_ioi_cv",
    ],
    "register_duration": [
        "mean_pitch",
        "std_pitch",
        "mean_note_duration_s",
        "mean_midi_ioi_s",
        "mtb_pitch_mean",
        "mtb_pitch_std",
        "mtb_duration_mean_s",
        "mtb_ioi_mean_s",
    ],
}

MODEL_FEATURES = [
    "onset_strength_mean",
    "mir_rms",
    "mir_brightness",
    "mir_roughness",
    "n_note_onsets",
    "approx_polyphony",
    "cv_midi_ioi",
    "mtb_ioi_cv",
]


def numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def rank_series(s: pd.Series) -> pd.Series:
    return s.rank(method="average", na_option="keep")


def pearson(x: pd.Series, y: pd.Series) -> tuple[float, float, int]:
    pair = pd.concat([x, y], axis=1).replace([np.inf, -np.inf], np.nan).dropna()
    n = len(pair)
    if n < 4:
        return np.nan, np.nan, n
    xv = pair.iloc[:, 0].to_numpy(dtype=float)
    yv = pair.iloc[:, 1].to_numpy(dtype=float)
    if np.nanstd(xv) == 0 or np.nanstd(yv) == 0:
        return np.nan, np.nan, n
    r = float(np.corrcoef(xv, yv)[0, 1])
    # Large-sample normal approximation for quick exploratory screening.
    z = abs(r) * math.sqrt(max(0, n - 3))
    p = math.erfc(z / math.sqrt(2))
    return r, p, n


def centered(df: pd.DataFrame, col: str, group_col: str) -> pd.Series:
    return df[col] - df.groupby(group_col)[col].transform("mean")


def zscore(s: pd.Series) -> pd.Series:
    sd = s.std(skipna=True)
    if not np.isfinite(sd) or sd == 0:
        return s * np.nan
    return (s - s.mean(skipna=True)) / sd


def correlation_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    all_features = [feature for group in FEATURE_GROUPS.values() for feature in group]
    for target in TARGETS:
        for group, features in FEATURE_GROUPS.items():
            for feature in features:
                if target not in df.columns or feature not in df.columns:
                    continue
                r, p, n = pearson(df[feature], df[target])
                sr, sp, sn = pearson(rank_series(df[feature]), rank_series(df[target]))
                tr, tp, tn = pearson(
                    centered(df, feature, "stim_name"),
                    centered(df, target, "stim_name"),
                )
                pr, pp, pn = pearson(
                    centered(df, feature, "wtc_code"),
                    centered(df, target, "wtc_code"),
                )
                rows.append(
                    {
                        "target": target,
                        "feature_group": group,
                        "feature": feature,
                        "n": n,
                        "pearson_r": r,
                        "pearson_p_approx": p,
                        "spearman_r": sr,
                        "spearman_p_approx": sp,
                        "within_track_pearson_r": tr,
                        "within_track_p_approx": tp,
                        "within_piece_pearson_r": pr,
                        "within_piece_p_approx": pp,
                        "usable_feature": feature in all_features,
                    }
                )
    out = pd.DataFrame(rows)
    if not out.empty:
        out["abs_within_track_r"] = out["within_track_pearson_r"].abs()
        out = out.sort_values(
            ["target", "abs_within_track_r", "spearman_r"],
            ascending=[True, False, False],
        )
    return out


def regression_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    available_features = [col for col in MODEL_FEATURES if col in df.columns]
    for target in TARGETS:
        cols = ["stim_name", "wtc_code", target] + available_features
        model_df = df[cols].replace([np.inf, -np.inf], np.nan).dropna()
        if len(model_df) < len(available_features) + 10:
            continue
        y = zscore(centered(model_df, target, "stim_name")).to_numpy(dtype=float)
        x_cols = []
        x_parts = []
        for feature in available_features:
            x = zscore(centered(model_df, feature, "stim_name")).to_numpy(dtype=float)
            if np.isfinite(x).sum() == len(x) and np.nanstd(x) > 0:
                x_cols.append(feature)
                x_parts.append(x)
        if not x_parts or not np.isfinite(y).all() or np.nanstd(y) == 0:
            continue
        xmat = np.column_stack([np.ones(len(y)), *x_parts])
        beta, *_ = np.linalg.lstsq(xmat, y, rcond=None)
        pred = xmat @ beta
        ss_res = float(np.sum((y - pred) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        for feature, coef in zip(x_cols, beta[1:]):
            rows.append(
                {
                    "target": target,
                    "feature": feature,
                    "standardized_beta_within_track": coef,
                    "model_r2_within_track": r2,
                    "n_complete_bins": len(model_df),
                    "n_tracks": model_df["stim_name"].nunique(),
                }
            )
    out = pd.DataFrame(rows)
    if not out.empty:
        out["abs_beta"] = out["standardized_beta_within_track"].abs()
        out = out.sort_values(["target", "abs_beta"], ascending=[True, False])
    return out


def same_piece_contrasts(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = [c for c in TARGETS + MODEL_FEATURES if c in df.columns]
    summary = (
        df.groupby(["wtc_code", "stim_name"], as_index=False)[numeric_cols]
        .median(numeric_only=True)
        .sort_values(["wtc_code", "stim_name"])
    )
    rows = []
    for wtc_code, group in summary.groupby("wtc_code"):
        if len(group) < 2:
            continue
        target_range = (
            group["istc_mean_max_unique_per_sec"].max()
            - group["istc_mean_max_unique_per_sec"].min()
            if "istc_mean_max_unique_per_sec" in group
            else np.nan
        )
        rows.append(
            {
                "wtc_code": wtc_code,
                "n_performances": len(group),
                "stim_names": "|".join(group["stim_name"].astype(str)),
                "median_istc_values": "|".join(
                    f"{v:.4g}" for v in group.get("istc_mean_max_unique_per_sec", pd.Series(dtype=float))
                ),
                "performance_range_median_istc": target_range,
                "median_onset_density_values": "|".join(
                    f"{v:.4g}" for v in group.get("note_onset_density_per_s", pd.Series(dtype=float))
                ),
                "median_mir_roughness_values": "|".join(
                    f"{v:.4g}" for v in group.get("mir_roughness", pd.Series(dtype=float))
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("performance_range_median_istc", ascending=False)


def write_plots(corr: pd.DataFrame) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - optional visualization
        print(f"Skipping plots; matplotlib unavailable: {exc}")
        return
    for target in TARGETS:
        sub = corr[corr["target"] == target].nlargest(12, "abs_within_track_r")
        if sub.empty:
            continue
        fig, ax = plt.subplots(figsize=(9, 5))
        labels = sub["feature"].tolist()
        vals = sub["within_track_pearson_r"].to_numpy()
        colors = ["#4c78a8" if v >= 0 else "#f58518" for v in vals]
        ax.barh(range(len(vals)), vals, color=colors)
        ax.set_yticks(range(len(vals)))
        ax.set_yticklabels(labels)
        ax.invert_yaxis()
        ax.axvline(0, color="black", linewidth=0.8)
        ax.set_xlabel("Within-track Pearson r")
        ax.set_title(f"Top time-varying feature associations: {target}")
        fig.tight_layout()
        fig.savefig(OUT_DIR / f"top_within_track_correlations_{target}.png", dpi=200)
        plt.close(fig)


def main() -> None:
    df = pd.read_csv(IN_TABLE)
    columns_to_numeric = TARGETS + [feature for group in FEATURE_GROUPS.values() for feature in group] + MODEL_FEATURES
    df = numeric(df, columns_to_numeric)

    corr = correlation_table(df)
    reg = regression_table(df)
    contrasts = same_piece_contrasts(df)

    corr.to_csv(OUT_DIR / "feature_coherence_correlations.csv", index=False)
    corr.groupby(["target", "feature_group"], as_index=False).agg(
        max_abs_within_track_r=("abs_within_track_r", "max"),
        median_abs_within_track_r=("abs_within_track_r", "median"),
        n_features=("feature", "count"),
    ).to_csv(OUT_DIR / "feature_group_correlation_summary.csv", index=False)
    reg.to_csv(OUT_DIR / "within_track_regression_summary.csv", index=False)
    contrasts.to_csv(OUT_DIR / "same_piece_exploratory_contrasts.csv", index=False)
    write_plots(corr)

    print(f"Wrote hypothesis outputs to {OUT_DIR}")
    print(f"Input rows: {len(df)}; tracks: {df['stim_name'].nunique()}; pieces: {df['wtc_code'].nunique()}")
    if not corr.empty:
        print("Top within-track associations:")
        print(
            corr.nlargest(8, "abs_within_track_r")[
                ["target", "feature", "within_track_pearson_r", "spearman_r", "n"]
            ].to_string(index=False)
        )


if __name__ == "__main__":
    main()
