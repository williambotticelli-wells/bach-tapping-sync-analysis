#!/usr/bin/env python3
"""Screen Nori whole-piece MIR features against per-track tapping coherence."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


BACH_ROOT = Path(__file__).resolve().parents[1]
MATLAB_ROOT = BACH_ROOT / "analysis" / "matlab_toolbox_features"
TAPPING_ROOT = BACH_ROOT / "analysis" / "beta_sync_tapping"
OUT_DIR = BACH_ROOT / "analysis" / "beta_sync_hypotheses"
OUT_DIR.mkdir(parents=True, exist_ok=True)

NORI_FEATURES = MATLAB_ROOT / "mirtoolbox_whole_piece_features.csv"
ISTC = TAPPING_ROOT / "istc_per_track.csv"
CONSENSUS = TAPPING_ROOT / "track_consensus_summary.csv"

TARGETS = [
    "istc_mean_max_unique_per_sec",
    "tap_count_mean_max_per_sec",
    "max_tap_count_per_100ms_bin",
    "consensus_tempo_bpm",
    "beat_sequence_cv_ioi_pct",
]


def pearson(x: pd.Series, y: pd.Series) -> tuple[float, float, int]:
    pair = pd.concat([x, y], axis=1).replace([np.inf, -np.inf], np.nan).dropna()
    n = len(pair)
    if n < 5:
        return np.nan, np.nan, n
    xv = pair.iloc[:, 0].to_numpy(dtype=float)
    yv = pair.iloc[:, 1].to_numpy(dtype=float)
    if np.nanstd(xv) == 0 or np.nanstd(yv) == 0:
        return np.nan, np.nan, n
    r = float(np.corrcoef(xv, yv)[0, 1])
    z = abs(r) * math.sqrt(max(0, n - 3))
    p = math.erfc(z / math.sqrt(2))
    return r, p, n


def main() -> None:
    features = pd.read_csv(NORI_FEATURES)
    istc = pd.read_csv(ISTC)
    consensus = pd.read_csv(CONSENSUS)
    targets = istc.merge(
        consensus[["stim_name", "consensus_tempo_bpm", "beat_sequence_cv_ioi_pct"]],
        on="stim_name",
        how="left",
    )
    df = features.merge(targets, on=["stim_name", "wtc_code"], how="inner", suffixes=("", "_target"))

    feature_cols = [
        col
        for col in features.columns
        if col not in {"stim_name", "wtc_code", "source_audio_path", "duration_s"}
    ]
    for col in feature_cols + TARGETS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    rows = []
    for target in TARGETS:
        if target not in df.columns:
            continue
        for feature in feature_cols:
            r, p, n = pearson(df[feature], df[target])
            sr, sp, sn = pearson(df[feature].rank(), df[target].rank())
            rows.append(
                {
                    "target": target,
                    "feature": feature,
                    "n_tracks": n,
                    "pearson_r": r,
                    "pearson_p_approx": p,
                    "spearman_r": sr,
                    "spearman_p_approx": sp,
                    "abs_pearson_r": abs(r) if np.isfinite(r) else np.nan,
                }
            )
    out = pd.DataFrame(rows).sort_values(["target", "abs_pearson_r"], ascending=[True, False])
    out.to_csv(OUT_DIR / "nori_whole_piece_feature_correlations.csv", index=False)

    top = out.groupby("target", group_keys=False).head(8)
    top.to_csv(OUT_DIR / "nori_whole_piece_top_correlations.csv", index=False)
    print(f"Wrote {OUT_DIR / 'nori_whole_piece_feature_correlations.csv'}")
    print(f"Wrote {OUT_DIR / 'nori_whole_piece_top_correlations.csv'}")
    print(f"Tracks: {df['stim_name'].nunique()}; features screened: {len(feature_cols)}")
    print(top[["target", "feature", "pearson_r", "spearman_r", "n_tracks"]].to_string(index=False))


if __name__ == "__main__":
    main()
