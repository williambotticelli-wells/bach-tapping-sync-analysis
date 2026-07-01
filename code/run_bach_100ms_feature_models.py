#!/usr/bin/env python3
"""Run 100 ms Bach MIDI/tapping feature screens.

Outputs are screening analyses for emotion/ECoG follow-up. They avoid
participant identifiers and use aggregate 100 ms bins.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


BACH_ROOT = Path(__file__).resolve().parents[1]
IN_100MS = BACH_ROOT / "analysis" / "beta_sync_100ms" / "bach_100ms_midi_tapping_feature_vectors.csv"
MIR_WHOLE = BACH_ROOT / "analysis" / "matlab_toolbox_features" / "mirtoolbox_whole_piece_features.csv"
MIDI_WHOLE = BACH_ROOT / "analysis" / "matlab_toolbox_features" / "miditoolbox_whole_piece_features.csv"
TRACK_COHERENCE = BACH_ROOT / "analysis" / "beta_sync_tapping" / "istc_per_track.csv"
OUT_DIR = BACH_ROOT / "analysis" / "beta_sync_100ms_models"

TARGETS_100MS = [
    "tap_count_100ms",
    "unique_tapper_count_100ms",
    "tap_density_per_s",
]

FEATURES_100MS = [
    "midi_note_onset_count_100ms",
    "midi_note_onset_density_per_s",
    "midi_active_note_count",
    "midi_active_note_density_per_s",
    "midi_pitch_min",
    "midi_pitch_max",
    "midi_pitch_range",
    "midi_pitch_mean",
    "midi_pitch_std",
    "midi_velocity_min",
    "midi_velocity_max",
    "midi_velocity_range",
    "midi_velocity_mean",
    "midi_velocity_std",
    "midi_dynamic_range",
]

TRACK_TARGETS = [
    "istc_mean_max_unique_per_sec",
    "tap_count_mean_max_per_sec",
    "max_unique_participants_per_100ms_bin",
    "max_tap_count_per_100ms_bin",
]


def bh_fdr(pvals: np.ndarray) -> np.ndarray:
    p = np.asarray(pvals, dtype=float)
    q = np.full_like(p, np.nan, dtype=float)
    mask = np.isfinite(p)
    if not mask.any():
        return q
    vals = p[mask]
    order = np.argsort(vals)
    ranked = vals[order]
    n = len(ranked)
    q_sorted = ranked * n / np.arange(1, n + 1)
    q_sorted = np.minimum.accumulate(q_sorted[::-1])[::-1]
    q_sorted = np.clip(q_sorted, 0, 1)
    restored = np.empty_like(q_sorted)
    restored[order] = q_sorted
    q[mask] = restored
    return q


def corr_screen(df: pd.DataFrame, targets: list[str], features: list[str], min_n: int) -> pd.DataFrame:
    rows = []
    for target in targets:
        for feature in features:
            if target not in df or feature not in df:
                continue
            sub = df[[target, feature]].replace([np.inf, -np.inf], np.nan).dropna()
            if len(sub) < min_n or sub[target].nunique() < 3 or sub[feature].nunique() < 3:
                continue
            pr, pp = pearsonr(sub[feature], sub[target])
            sr, sp = spearmanr(sub[feature], sub[target])
            rows.append(
                {
                    "target": target,
                    "feature": feature,
                    "n": len(sub),
                    "pearson_r": pr,
                    "pearson_p": pp,
                    "spearman_rho": sr,
                    "spearman_p": sp,
                }
            )
    out = pd.DataFrame(rows)
    if not out.empty:
        out["spearman_fdr_q"] = bh_fdr(out["spearman_p"].to_numpy())
        out["abs_spearman_rho"] = out["spearman_rho"].abs()
        out = out.sort_values(["target", "abs_spearman_rho"], ascending=[True, False])
    return out


def centered_within_track(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col in out:
            out[col] = out[col] - out.groupby("stim_name")[col].transform("mean")
    return out


def ols_univariate(df: pd.DataFrame, targets: list[str], features: list[str], min_n: int) -> pd.DataFrame:
    rows = []
    for target in targets:
        for feature in features:
            sub = df[[target, feature]].replace([np.inf, -np.inf], np.nan).dropna()
            if len(sub) < min_n or sub[target].nunique() < 3 or sub[feature].nunique() < 3:
                continue
            x = sub[feature].to_numpy(float)
            y = sub[target].to_numpy(float)
            xz = (x - x.mean()) / (x.std(ddof=1) + 1e-12)
            yz = (y - y.mean()) / (y.std(ddof=1) + 1e-12)
            X = np.column_stack([np.ones(len(xz)), xz])
            beta, *_ = np.linalg.lstsq(X, yz, rcond=None)
            pred = X @ beta
            resid = yz - pred
            s2 = float(np.sum(resid**2) / max(1, len(yz) - 2))
            cov = s2 * np.linalg.inv(X.T @ X)
            se = float(np.sqrt(cov[1, 1]))
            t = float(beta[1] / (se + 1e-12))
            r2 = float(1.0 - np.sum(resid**2) / (np.sum((yz - yz.mean()) ** 2) + 1e-12))
            rows.append(
                {
                    "target": target,
                    "feature": feature,
                    "n": len(sub),
                    "standardized_beta": float(beta[1]),
                    "se": se,
                    "t": t,
                    "r2": r2,
                }
            )
    out = pd.DataFrame(rows)
    if not out.empty:
        out["abs_beta"] = out["standardized_beta"].abs()
        out = out.sort_values(["target", "abs_beta"], ascending=[True, False])
    return out


def bayesian_ridge_multifeature(df: pd.DataFrame, target: str, features: list[str]) -> pd.DataFrame:
    cols = [target] + [f for f in features if f in df]
    sub = df[cols].replace([np.inf, -np.inf], np.nan).dropna()
    if len(sub) < 100:
        return pd.DataFrame()
    X = sub[features].to_numpy(float)
    y = sub[target].to_numpy(float)
    X = (X - X.mean(axis=0)) / (X.std(axis=0, ddof=1) + 1e-12)
    y = (y - y.mean()) / (y.std(ddof=1) + 1e-12)
    alpha = 1.0
    XtX = X.T @ X
    precision = XtX + alpha * np.eye(X.shape[1])
    cov = np.linalg.inv(precision)
    beta = cov @ X.T @ y
    resid = y - X @ beta
    sigma2 = float(np.sum(resid**2) / max(1, len(y) - X.shape[1]))
    post_sd = np.sqrt(np.diag(cov) * sigma2)
    draws = np.random.default_rng(20260701).normal(beta, post_sd, size=(20000, len(beta)))
    rows = []
    for i, feature in enumerate(features):
        rows.append(
            {
                "target": target,
                "feature": feature,
                "posterior_mean_beta": float(beta[i]),
                "posterior_sd": float(post_sd[i]),
                "posterior_p_beta_gt_0": float(np.mean(draws[:, i] > 0)),
                "posterior_p_direction": float(max(np.mean(draws[:, i] > 0), np.mean(draws[:, i] < 0))),
            }
        )
    out = pd.DataFrame(rows)
    out["abs_posterior_mean_beta"] = out["posterior_mean_beta"].abs()
    return out.sort_values(["target", "posterior_p_direction", "abs_posterior_mean_beta"], ascending=[True, False, False])


def track_level_whole_piece_screen() -> pd.DataFrame:
    coh = pd.read_csv(TRACK_COHERENCE)
    mir = pd.read_csv(MIR_WHOLE)
    midi = pd.read_csv(MIDI_WHOLE)
    merged = coh.merge(mir, on=["stim_name", "wtc_code"], how="left").merge(
        midi, on=["stim_name", "wtc_code"], how="left", suffixes=("", "_midi")
    )
    feature_cols = [
        c
        for c in merged.columns
        if c not in {"stim_name", "wtc_code", "source_audio_path", "midi_path"}
        and c not in TRACK_TARGETS
        and pd.api.types.is_numeric_dtype(merged[c])
        and merged[c].notna().sum() >= 12
        and merged[c].nunique(dropna=True) > 3
    ]
    out = corr_screen(merged, TRACK_TARGETS, feature_cols, min_n=12)
    merged.to_csv(OUT_DIR / "bach_track_level_mir_midi_coherence_table.csv", index=False)
    return out


def write_summary(global_corr: pd.DataFrame, within_corr: pd.DataFrame, bayes: pd.DataFrame, track_corr: pd.DataFrame) -> None:
    lines = [
        "# Bach 100 ms Feature Modeling Summary",
        "",
        "These are screening analyses for MIDI/MIR/tapping feature relationships.",
        "",
        "## 100 ms Within-Track Signals",
        "",
    ]
    for target, sub in within_corr.groupby("target"):
        lines.append(f"### {target}")
        for _, row in sub.head(6).iterrows():
            lines.append(
                f"- `{row['feature']}`: Spearman rho={row['spearman_rho']:.3f}, q={row['spearman_fdr_q']:.3g}, n={int(row['n'])}."
            )
        lines.append("")
    lines.append("## Bayesian Ridge Direction Screen")
    lines.append("")
    for target, sub in bayes.groupby("target"):
        lines.append(f"### {target}")
        for _, row in sub.head(6).iterrows():
            lines.append(
                f"- `{row['feature']}`: beta={row['posterior_mean_beta']:.3f}, P(direction)={row['posterior_p_direction']:.3f}."
            )
        lines.append("")
    lines.append("## Whole-Piece MIR/MIDI vs Track Coherence")
    lines.append("")
    for target, sub in track_corr.groupby("target"):
        lines.append(f"### {target}")
        for _, row in sub.head(5).iterrows():
            lines.append(
                f"- `{row['feature']}`: Spearman rho={row['spearman_rho']:.3f}, q={row['spearman_fdr_q']:.3g}, n={int(row['n'])}."
            )
        lines.append("")
    (OUT_DIR / "bach_100ms_feature_modeling_summary.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(IN_100MS, low_memory=False)
    global_corr = corr_screen(df, TARGETS_100MS, FEATURES_100MS, min_n=100)
    within = centered_within_track(df, TARGETS_100MS + FEATURES_100MS)
    within_corr = corr_screen(within, TARGETS_100MS, FEATURES_100MS, min_n=100)
    ols = ols_univariate(within, TARGETS_100MS, FEATURES_100MS, min_n=100)
    bayes_rows = []
    for target in TARGETS_100MS:
        bayes_rows.append(bayesian_ridge_multifeature(within, target, FEATURES_100MS))
    bayes = pd.concat([b for b in bayes_rows if not b.empty], ignore_index=True)
    track_corr = track_level_whole_piece_screen()
    global_corr.to_csv(OUT_DIR / "bach_100ms_global_correlations.csv", index=False)
    within_corr.to_csv(OUT_DIR / "bach_100ms_within_track_correlations.csv", index=False)
    ols.to_csv(OUT_DIR / "bach_100ms_within_track_univariate_regressions.csv", index=False)
    bayes.to_csv(OUT_DIR / "bach_100ms_within_track_bayesian_ridge_screen.csv", index=False)
    track_corr.to_csv(OUT_DIR / "bach_track_level_mir_midi_coherence_correlations.csv", index=False)
    write_summary(global_corr, within_corr, bayes, track_corr)
    print(OUT_DIR / "bach_100ms_feature_modeling_summary.md")


if __name__ == "__main__":
    main()
