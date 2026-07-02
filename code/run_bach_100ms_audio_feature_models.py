#!/usr/bin/env python3
"""Screen 100 ms Bach acoustic/MIR features against tapping concentration."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


BACH_ROOT = Path(__file__).resolve().parents[1]
IN_MIDI_TAP = BACH_ROOT / "analysis" / "beta_sync_100ms" / "bach_100ms_midi_tapping_feature_vectors.csv"
IN_AUDIO = BACH_ROOT / "analysis" / "beta_sync_100ms" / "bach_100ms_audio_feature_vectors.csv"
IN_JOINED = BACH_ROOT / "analysis" / "beta_sync_100ms" / "bach_100ms_audio_midi_tapping_feature_vectors.csv"
IN_MIRTOOLBOX = BACH_ROOT / "analysis" / "matlab_toolbox_features" / "mirtoolbox_100ms_features.csv"
OUT_DIR = BACH_ROOT / "analysis" / "beta_sync_100ms_models"

TARGETS = ["tap_count_100ms"]
KEYS = ["stim_name", "wtc_code", "bin_index", "bin_start_s", "bin_end_s", "bin_center_s"]
NON_FEATURE_COLS = set(KEYS + ["bin_width_s", "source_audio_path"])


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


def available_feature_cols(df: pd.DataFrame) -> list[str]:
    cols = []
    for col in df.columns:
        if col in NON_FEATURE_COLS or col in TARGETS:
            continue
        if not col.startswith(("audio100_", "mir100_")):
            continue
        if pd.api.types.is_numeric_dtype(df[col]) and df[col].notna().sum() >= 100 and df[col].nunique(dropna=True) > 3:
            cols.append(col)
    return cols


def load_audio_features() -> tuple[pd.DataFrame, str]:
    if IN_MIRTOOLBOX.exists():
        return pd.read_csv(IN_MIRTOOLBOX, low_memory=False), "mirtoolbox_100ms"
    return pd.read_csv(IN_AUDIO, low_memory=False), "python_audio_100ms"


def write_summary(source_label: str, global_corr: pd.DataFrame, within_corr: pd.DataFrame, feature_cols: list[str]) -> None:
    lines = [
        "# Bach 100 ms Acoustic/MIR Feature Screen",
        "",
        f"- Feature source: `{source_label}`.",
        f"- Features screened: {len(feature_cols)}.",
        "- The within-track rows are the main local-effect screen; global rows are context.",
        "",
        "## Top Within-Track Associations",
        "",
    ]
    if within_corr.empty:
        lines.append("No within-track correlations met the screening criteria.")
    else:
        for _, row in within_corr.head(8).iterrows():
            lines.append(
                f"- `{row['feature']}`: Spearman rho={row['spearman_rho']:.3f}, q={row['spearman_fdr_q']:.3g}, n={int(row['n'])}."
            )
    lines.extend(["", "## Top Global Associations", ""])
    if global_corr.empty:
        lines.append("No global correlations met the screening criteria.")
    else:
        for _, row in global_corr.head(8).iterrows():
            lines.append(
                f"- `{row['feature']}`: Spearman rho={row['spearman_rho']:.3f}, q={row['spearman_fdr_q']:.3g}, n={int(row['n'])}."
            )
    (OUT_DIR / "bach_100ms_audio_feature_modeling_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if IN_JOINED.exists():
        joined = pd.read_csv(IN_JOINED, low_memory=False)
        source_label = "joined_100ms_audio_midi_tapping"
    else:
        midi_tap = pd.read_csv(IN_MIDI_TAP, low_memory=False)
        audio, source_label = load_audio_features()
        merge_keys = [key for key in KEYS if key in midi_tap.columns and key in audio.columns]
        joined = midi_tap.merge(audio, on=merge_keys, how="left", suffixes=("", "_audio"))
    feature_cols = available_feature_cols(joined)
    global_corr = corr_screen(joined, TARGETS, feature_cols, min_n=100)
    within = centered_within_track(joined, TARGETS + feature_cols)
    within_corr = corr_screen(within, TARGETS, feature_cols, min_n=100)

    global_corr.to_csv(OUT_DIR / "bach_100ms_audio_global_correlations.csv", index=False)
    within_corr.to_csv(OUT_DIR / "bach_100ms_audio_within_track_correlations.csv", index=False)
    write_summary(source_label, global_corr, within_corr, feature_cols)
    print(OUT_DIR / "bach_100ms_audio_feature_modeling_summary.md")


if __name__ == "__main__":
    main()
