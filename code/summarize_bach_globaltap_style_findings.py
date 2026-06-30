#!/usr/bin/env python3
"""Summarize candidate scientific signals from Bach GlobalTap-style outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


BACH_ROOT = Path(__file__).resolve().parents[1]
GT_OUT = BACH_ROOT / "analysis" / "beta_globaltap_canonical"
MATLAB_OUT = BACH_ROOT / "analysis" / "matlab_toolbox_features"
SYNC_OUT = BACH_ROOT / "analysis" / "beta_sync_tapping"
REPORT = GT_OUT / "candidate_scientific_findings.md"


TARGETS = [
    "kde_curve_r_mean",
    "peak_f_mean",
    "sample_size_for_kde_r_ge_0p9",
    "optimized_tempo_bpm",
    "midi_onset_f_measure_diagnostic",
]


def numeric_feature_cols(df: pd.DataFrame) -> list[str]:
    skip = {
        "stim_name",
        "wtc_code",
        "source_audio_path",
        "midi_path",
        "click_preview_path",
        "comparison",
        "optimizer_path",
        "optimizer_label",
    }
    cols = []
    for col in df.columns:
        if col in skip:
            continue
        if pd.api.types.is_numeric_dtype(df[col]) and df[col].notna().sum() >= 10 and df[col].nunique(dropna=True) > 2:
            cols.append(col)
    return cols


def correlation_screen(df: pd.DataFrame, targets: list[str], features: list[str]) -> pd.DataFrame:
    rows = []
    for target in targets:
        if target not in df.columns:
            continue
        for feature in features:
            if feature == target:
                continue
            sub = df[[target, feature]].replace([np.inf, -np.inf], np.nan).dropna()
            if len(sub) < 8 or sub[target].nunique() < 3 or sub[feature].nunique() < 3:
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--globaltap-dir", default=str(GT_OUT))
    args = parser.parse_args()
    globaltap_dir = Path(args.globaltap_dir)
    report = globaltap_dir / "candidate_scientific_findings.md"

    track = pd.read_csv(globaltap_dir / "bach_globaltap_style_track_summary.csv")
    split = pd.read_csv(globaltap_dir / "split_half_reliability_first30s.csv")
    conv = pd.read_csv(globaltap_dir / "convergence_to_full_density_first30s.csv")
    mir = pd.read_csv(MATLAB_OUT / "mirtoolbox_whole_piece_features.csv")
    midi = pd.read_csv(MATLAB_OUT / "miditoolbox_whole_piece_features.csv")
    consensus = pd.read_csv(SYNC_OUT / "track_consensus_summary.csv")

    thresholds = convergence_thresholds(conv)
    joined = track.merge(split, on="stim_name", how="left", suffixes=("", "_split"))
    joined = joined.merge(thresholds, on="stim_name", how="left")
    joined = joined.merge(consensus, on="stim_name", how="left", suffixes=("", "_consensus"))
    joined = joined.merge(mir, on=["stim_name", "wtc_code"], how="left", suffixes=("", "_mir"))
    joined = joined.merge(midi, on=["stim_name", "wtc_code"], how="left", suffixes=("", "_midi"))
    joined.to_csv(globaltap_dir / "bach_globaltap_style_joined_track_features.csv", index=False)

    features = [col for col in numeric_feature_cols(joined) if col not in TARGETS]
    corrs = correlation_screen(joined, TARGETS, features)
    corrs.to_csv(globaltap_dir / "candidate_feature_correlations_with_globaltap_metrics.csv", index=False)

    top_reliable = split.sort_values("kde_curve_r_mean", ascending=False).head(8)
    low_reliable = split.sort_values("kde_curve_r_mean", ascending=True).head(8)
    top_corrs = corrs.groupby("target", group_keys=False).head(6)

    piece = (
        joined.groupby("wtc_code")
        .agg(
            n_performances=("stim_name", "count"),
            stim_names=("stim_name", lambda x: "|".join(sorted(map(str, x)))),
            median_split_half_kde_r=("kde_curve_r_mean", "median"),
            median_sample_size_for_r90=("sample_size_for_kde_r_ge_0p9", "median"),
            tempo_range_bpm=("optimized_tempo_bpm", lambda x: float(np.nanmax(x) - np.nanmin(x)) if x.notna().sum() > 1 else np.nan),
        )
        .reset_index()
        .sort_values("median_split_half_kde_r", ascending=False)
    )
    piece.to_csv(globaltap_dir / "same_piece_globaltap_style_summary.csv", index=False)

    lines = [
        "# Candidate Bach GlobalTap-Style Findings",
        "",
        "These are screening results from the first 30 s of each Bach stimulus, matching the GlobalTap excerpt window more closely than the full-piece exploratory tables.",
        "",
        "## Reliability Signal",
        "",
        f"- Median split-half KDE correlation: {split['kde_curve_r_mean'].median():.3f}.",
        f"- Median split-half peak F-measure: {split['peak_f_mean'].median():.3f}.",
        f"- Most reliable tracks: {', '.join(top_reliable['stim_name'].tolist())}.",
        f"- Weakest reliability tracks: {', '.join(low_reliable['stim_name'].tolist())}.",
        "",
        "## Convergence Signal",
        "",
        f"- Median participant count to reach KDE r >= .90 against the full crowd: {thresholds['sample_size_for_kde_r_ge_0p9'].median():.1f}.",
        f"- Fastest convergence: {', '.join(thresholds.sort_values('sample_size_for_kde_r_ge_0p9').head(5)['stim_name'].tolist())}.",
        f"- Slowest convergence: {', '.join(thresholds.sort_values('sample_size_for_kde_r_ge_0p9', ascending=False).head(5)['stim_name'].tolist())}.",
        "",
        "## Top Feature Screens",
        "",
    ]
    for target, sub in top_corrs.groupby("target"):
        lines.append(f"### {target}")
        for _, row in sub.head(5).iterrows():
            lines.append(
                f"- `{row['feature']}`: Spearman rho={row['spearman_rho']:.3f}, Pearson r={row['pearson_r']:.3f}, n={int(row['n'])}."
            )
        lines.append("")
    lines.extend(
        [
            "## Same-Piece/Performance Notes",
            "",
            f"- Unique WTC codes in this manifest: {piece['wtc_code'].nunique()}.",
            f"- WTC codes with exactly two performances: {(piece['n_performances'] == 2).sum()}.",
            "- `same_piece_globaltap_style_summary.csv` lists each piece's two-performance grouping and reliability/tempo spread.",
            "",
            "## Caveats",
            "",
            "- The optimized grid here uses the companion-repo GlobalTap optimizer cascade.",
            "- MIDI-onset F-measure is an event/synchronization diagnostic, not a ground-truth beat-tracker benchmark.",
            "- The strongest shareable result remains the tapping reliability/convergence pattern plus its relationship to MIR/MIDI feature screens; emotion and ECoG joins remain future data gates.",
        ]
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
