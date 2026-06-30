#!/usr/bin/env python3
"""Compare canonical Bach optimizer outputs with MIR/MIDI features.

This script bridges two analysis levels:

1. Whole-piece/track-level relationships between optimizer diagnostics
   (bimodality, balanced-lambda fallback, convergence, split-half reliability)
   and whole-piece MIRToolbox/MIDI Toolbox features.
2. Time-binned relationships between local optimizer fit behavior
   (MAD-filtered KDE peak density, optimized beat density, peak-to-grid error)
   and time-binned MIR/MIDI/audio/tapping features.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


BACH_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = BACH_ROOT / "analysis" / "beta_globaltap_canonical"
MULTIMODAL = BACH_ROOT / "analysis" / "beta_sync_multimodal" / "bach_time_binned_multimodal_with_matlab_toolboxes.csv"
MATLAB = BACH_ROOT / "analysis" / "matlab_toolbox_features"
CONSENSUS = BACH_ROOT / "analysis" / "beta_sync_tapping" / "track_consensus_summary.csv"
REPORT = CANONICAL / "optimizer_feature_relationships.md"

TRACK_TARGETS = [
    "kde_curve_r_mean",
    "peak_f_mean",
    "sample_size_for_kde_r_ge_0p9",
    "sample_size_for_peak_f_ge_0p8",
    "optimized_beat_cv_ioi",
    "bimodal_score",
    "midi_onset_f_measure_diagnostic",
    "used_bimodal_route",
    "used_balanced_lambdas",
]

WINDOW_TARGETS = [
    "optimizer_peak_density_per_s",
    "optimizer_beat_density_per_s",
    "optimizer_peak_coverage_70ms",
    "optimizer_peak_to_grid_median_abs_error_ms",
    "istc_mean_max_unique_per_sec",
    "max_unique_participants_per_100ms_bin",
    "max_tap_count_per_100ms_bin",
]

META_COLS = {
    "stim_name",
    "wtc_code",
    "manifest_wtc_code",
    "source_audio_path",
    "midi_path",
    "click_preview_path",
    "optimizer_path",
    "optimizer_label",
    "comparison",
}


def numeric_cols(df: pd.DataFrame, min_n: int = 10) -> list[str]:
    cols = []
    for col in df.columns:
        if col in META_COLS:
            continue
        if pd.api.types.is_numeric_dtype(df[col]) and df[col].notna().sum() >= min_n and df[col].nunique(dropna=True) > 2:
            cols.append(col)
    return cols


def corr_screen(df: pd.DataFrame, targets: list[str], features: list[str], min_n: int = 8) -> pd.DataFrame:
    rows = []
    for target in targets:
        if target not in df.columns:
            continue
        for feature in features:
            if feature == target:
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
                    "abs_spearman_rho": abs(sr),
                }
            )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["target", "abs_spearman_rho"], ascending=[True, False])


def convergence_thresholds(conv: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for stim, sub in conv.groupby("stim_name"):
        sub = sub.sort_values("sample_size")
        row = {"stim_name": stim}
        for metric, thresh, label in [
            ("kde_curve_r_to_full_mean", 0.90, "sample_size_for_kde_r_ge_0p9"),
            ("peak_f_to_full_mean", 0.80, "sample_size_for_peak_f_ge_0p8"),
        ]:
            hit = sub[sub[metric] >= thresh]
            row[label] = int(hit.iloc[0]["sample_size"]) if not hit.empty else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def load_optimizer_diagnostics(path: Path) -> pd.DataFrame:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            path_items = row.get("path", [])
            scores = row.get("scores", {}) or {}
            rows.append(
                {
                    "stim_name": row.get("stem", ""),
                    "P_std": row.get("P_std", np.nan),
                    "cv_std": row.get("cv_std", np.nan),
                    "crowd_P": row.get("crowd_P", np.nan),
                    "crowd_cv": row.get("crowd_cv", np.nan),
                    "crowd_n_beats": row.get("crowd_n_beats", np.nan),
                    "diag_bimodal_score": row.get("bimodal_score", np.nan),
                    "used_bimodal_route": int(any(str(x).startswith("bimodal") for x in path_items)),
                    "used_balanced_lambdas": int(any("balanced" in str(x) for x in path_items)),
                    "used_grid_extension": int(any("GE_applied" in str(x) for x in path_items)),
                    "balanced_score": scores.get("balanced", np.nan),
                    "std_score": scores.get("std", np.nan),
                    "monoA_score": scores.get("monoA", np.nan),
                    "monoB_score": scores.get("monoB", np.nan),
                }
            )
    return pd.DataFrame(rows)


def build_track_table(canonical_dir: Path) -> pd.DataFrame:
    track = pd.read_csv(canonical_dir / "bach_globaltap_style_track_summary.csv")
    split = pd.read_csv(canonical_dir / "split_half_reliability_first30s.csv")
    conv = pd.read_csv(canonical_dir / "convergence_to_full_density_first30s.csv")
    diag = load_optimizer_diagnostics(canonical_dir / "optimizer_diagnostics.jsonl")
    mir = pd.read_csv(MATLAB / "mirtoolbox_whole_piece_features.csv")
    midi = pd.read_csv(MATLAB / "miditoolbox_whole_piece_features.csv")
    consensus = pd.read_csv(CONSENSUS)

    joined = track.merge(split, on="stim_name", how="left", suffixes=("", "_split"))
    joined = joined.merge(convergence_thresholds(conv), on="stim_name", how="left")
    joined = joined.merge(diag, on="stim_name", how="left", suffixes=("", "_diag"))
    joined = joined.merge(consensus, on="stim_name", how="left", suffixes=("", "_consensus"))
    joined = joined.merge(mir, on=["stim_name", "wtc_code"], how="left", suffixes=("", "_mir"))
    joined = joined.merge(midi, on=["stim_name", "wtc_code"], how="left", suffixes=("", "_midi"))
    return joined


def nearest_distance(values: np.ndarray, refs: np.ndarray) -> np.ndarray:
    if values.size == 0 or refs.size == 0:
        return np.full(values.size, np.nan)
    return np.min(np.abs(values[:, None] - refs[None, :]), axis=1)


def build_window_optimizer_metrics(canonical_dir: Path, windows: pd.DataFrame) -> pd.DataFrame:
    peaks = pd.read_csv(canonical_dir / "mad_filtered_kde_peaks_first30s.csv")
    beats = pd.read_csv(canonical_dir / "optimized_crowd_beats_first30s.csv")
    rows = []
    for _, win in windows[["stim_name", "wtc_code", "window_start_s", "window_end_s", "window_center_s"]].drop_duplicates().iterrows():
        stim = win["stim_name"]
        w0 = float(win["window_start_s"])
        w1 = float(win["window_end_s"])
        if w0 >= 30.0:
            continue
        peak_vals = peaks.loc[
            (peaks["stim_name"] == stim)
            & (peaks["filtered_kde_peak_s"] >= w0)
            & (peaks["filtered_kde_peak_s"] < w1),
            "filtered_kde_peak_s",
        ].to_numpy(float)
        beat_vals = beats.loc[
            (beats["stim_name"] == stim)
            & (beats["optimized_crowd_beat_s"] >= w0)
            & (beats["optimized_crowd_beat_s"] < w1),
            "optimized_crowd_beat_s",
        ].to_numpy(float)
        all_beats = beats.loc[beats["stim_name"] == stim, "optimized_crowd_beat_s"].to_numpy(float)
        dists = nearest_distance(peak_vals, all_beats)
        duration = max(1e-9, w1 - w0)
        rows.append(
            {
                "stim_name": stim,
                "wtc_code": win["wtc_code"],
                "window_start_s": w0,
                "window_end_s": w1,
                "window_center_s": float(win["window_center_s"]),
                "optimizer_peak_count": int(peak_vals.size),
                "optimizer_beat_count": int(beat_vals.size),
                "optimizer_peak_density_per_s": float(peak_vals.size / duration),
                "optimizer_beat_density_per_s": float(beat_vals.size / duration),
                "optimizer_peak_coverage_70ms": float(np.nanmean(dists <= 0.070)) if dists.size else np.nan,
                "optimizer_peak_to_grid_median_abs_error_ms": float(np.nanmedian(dists) * 1000.0) if dists.size else np.nan,
                "optimizer_peak_to_grid_mean_abs_error_ms": float(np.nanmean(dists) * 1000.0) if dists.size else np.nan,
            }
        )
    return pd.DataFrame(rows)


def feature_columns_for_windows(df: pd.DataFrame) -> list[str]:
    blocked = set(WINDOW_TARGETS) | {
        "window_start_s",
        "window_end_s",
        "window_center_s",
        "optimizer_peak_count",
        "optimizer_beat_count",
        "n_participants",
        "n_trials",
        "n_consensus_peaks",
        "consensus_median_ioi_s",
        "beat_sequence_cv_ioi_pct",
        "consensus_tempo_bpm",
        "beta_perf",
        "beta_score",
        "beta_list",
        "tap_count_mean_max_per_sec",
        "optimizer_peak_count",
        "optimizer_beat_count",
        "optimizer_peak_to_grid_mean_abs_error_ms",
    }
    return [col for col in numeric_cols(df, min_n=100) if col not in blocked]


def feature_columns_for_tracks(df: pd.DataFrame) -> list[str]:
    blocked_prefixes = (
        "optimized_",
        "optimizer_",
        "crowd_",
        "diag_",
        "used_",
        "mono",
    )
    blocked_exact = set(TRACK_TARGETS) | {
        "analysis_window_start_s",
        "analysis_window_end_s",
        "n_participants",
        "n_raw_taps_window",
        "n_filtered_taps_window",
        "tap_retention_after_mad",
        "n_filtered_kde_peaks",
        "n_optimized_beats",
        "grid_extension_activated",
        "P_std",
        "cv_std",
        "balanced_score",
        "std_score",
        "sample_size_for_kde_r_ge_0p9",
        "sample_size_for_peak_f_ge_0p8",
        "split_iterations",
        "kde_curve_r_sd",
        "peak_f_sd",
    }
    return [
        col
        for col in numeric_cols(df, min_n=10)
        if col not in blocked_exact and not any(col.startswith(prefix) for prefix in blocked_prefixes)
    ]


def within_track_corrs(df: pd.DataFrame, targets: list[str], features: list[str]) -> pd.DataFrame:
    centered = df.copy()
    for col in [c for c in set(targets + features) if c in centered.columns and pd.api.types.is_numeric_dtype(centered[c])]:
        centered[col] = centered[col] - centered.groupby("stim_name")[col].transform("mean")
    return corr_screen(centered, targets, features, min_n=100)


def write_report(track_corrs: pd.DataFrame, window_corrs: pd.DataFrame, window_within: pd.DataFrame, track_table: pd.DataFrame, path: Path) -> None:
    lines = [
        "# Optimizer Feature Relationship Screens",
        "",
        "These screens compare canonical GlobalTap optimizer outputs with MIRToolbox and MIDI Toolbox features at whole-piece and time-binned levels.",
        "",
        "## Optimizer Path Summary",
        "",
        f"- Tracks analyzed: {track_table['stim_name'].nunique()}",
        f"- Bimodal route used: {int(track_table['used_bimodal_route'].sum())} tracks",
        f"- Balanced-lambda route used: {int(track_table['used_balanced_lambdas'].sum())} tracks",
        f"- Grid extension applied: {int(track_table['used_grid_extension'].sum())} tracks",
        "",
        "## Strongest Whole-Piece Screens",
        "",
    ]
    for target, sub in track_corrs.groupby("target"):
        lines.append(f"### {target}")
        for _, row in sub.head(5).iterrows():
            lines.append(
                f"- `{row['feature']}`: Spearman rho={row['spearman_rho']:.3f}, Pearson r={row['pearson_r']:.3f}, n={int(row['n'])}."
            )
        lines.append("")
    lines.append("## Strongest Time-Binned Screens")
    lines.append("")
    for target, sub in window_corrs.groupby("target"):
        lines.append(f"### {target}")
        for _, row in sub.head(5).iterrows():
            lines.append(
                f"- `{row['feature']}`: Spearman rho={row['spearman_rho']:.3f}, Pearson r={row['pearson_r']:.3f}, n={int(row['n'])}."
            )
        lines.append("")
    lines.append("## Strongest Within-Track Time-Binned Screens")
    lines.append("")
    for target, sub in window_within.groupby("target"):
        lines.append(f"### {target}")
        for _, row in sub.head(5).iterrows():
            lines.append(
                f"- `{row['feature']}`: within-track Spearman rho={row['spearman_rho']:.3f}, Pearson r={row['pearson_r']:.3f}, n={int(row['n'])}."
            )
        lines.append("")
    lines.extend(
        [
            "## Interpretation Guardrails",
            "",
            "- Time-binned rows overlap heavily, so p-values are screening diagnostics rather than inferential claims.",
            "- MIDI-onset agreement remains an event/synchronization diagnostic, not a beat-reference benchmark.",
            "- Participant-level data are not required for these screens; all outputs here are aggregate or feature-level.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-dir", default=str(CANONICAL))
    args = parser.parse_args()
    canonical_dir = Path(args.canonical_dir)

    track_table = build_track_table(canonical_dir)
    track_features = feature_columns_for_tracks(track_table)
    track_corrs = corr_screen(track_table, TRACK_TARGETS, track_features, min_n=8)

    windows = pd.read_csv(MULTIMODAL, low_memory=False)
    windows = windows[windows["window_start_s"] < 30.0].copy()
    optimizer_windows = build_window_optimizer_metrics(canonical_dir, windows)
    window_joined = windows.merge(
        optimizer_windows,
        on=["stim_name", "wtc_code", "window_start_s", "window_end_s", "window_center_s"],
        how="left",
    )
    window_features = feature_columns_for_windows(window_joined)
    window_corrs = corr_screen(window_joined, WINDOW_TARGETS, window_features, min_n=100)
    window_within = within_track_corrs(window_joined, WINDOW_TARGETS, window_features)

    track_table.to_csv(canonical_dir / "optimizer_whole_piece_feature_table.csv", index=False)
    track_corrs.to_csv(canonical_dir / "optimizer_whole_piece_feature_correlations.csv", index=False)
    optimizer_windows.to_csv(canonical_dir / "optimizer_time_binned_metrics_first30s.csv", index=False)
    window_joined.to_csv(canonical_dir / "optimizer_time_binned_feature_table_first30s.csv", index=False)
    window_corrs.to_csv(canonical_dir / "optimizer_time_binned_feature_correlations.csv", index=False)
    window_within.to_csv(canonical_dir / "optimizer_time_binned_within_track_correlations.csv", index=False)
    write_report(track_corrs, window_corrs, window_within, track_table, canonical_dir / "optimizer_feature_relationships.md")
    print(canonical_dir / "optimizer_feature_relationships.md")


if __name__ == "__main__":
    main()
