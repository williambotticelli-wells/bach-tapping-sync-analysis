#!/usr/bin/env python3
"""Track-level (song-wide, n=24 tracks) emotion vs. whole-piece MIR/MIDI and
tapping-coherence screen, run separately per emotion (n=24 per emotion, or
n=96 pooled with emotion as a factor).

n=24 is genuinely small (same caveat the existing repo already applies to its
own whole-piece MIR/MIDI vs coherence screens -- "n=24 is too small for
strong claims", bach-project-audit-2026-06-30.md). Results here are
exploratory leads, not confirmatory. Reuses the base script's `corr_screen`
/ `bh_fdr` for consistency; univariate OLS and Bayesian ridge are skipped at
this n given how unstable multi-feature fits get with p >> n (there are ~185
candidate whole-piece features and n=24).

Inputs:
  - tables/analysis__beta_sync_emotion__bach_track_level_emotion_tapping_mir_midi_summary.csv

Outputs:
  - tables/analysis__beta_sync_emotion_models__bach_track_level_emotion_correlations.csv
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "code"
IN_PATH = (
    REPO_ROOT
    / "tables"
    / "analysis__beta_sync_emotion__bach_track_level_emotion_tapping_mir_midi_summary.csv"
)
OUT_PATH = (
    REPO_ROOT
    / "tables"
    / "analysis__beta_sync_emotion_models__bach_track_level_emotion_correlations.csv"
)

spec = importlib.util.spec_from_file_location(
    "run_bach_100ms_feature_models", CODE_DIR / "run_bach_100ms_feature_models.py"
)
base = importlib.util.module_from_spec(spec)
sys.modules["run_bach_100ms_feature_models"] = base
spec.loader.exec_module(base)

EMOTIONS = ["happy", "sad", "calm", "energetic"]
NON_FEATURE_COLS = {
    "stim_name",
    "wtc_code",
    "emotion_term",
    "emotion_rating_mean",
    "emotion_rating_sd",
    "emotion_rating_min",
    "emotion_rating_max",
    "emotion_rating_se",
    "mean_within_trial_sd",
    "n_participants",
    "manifest_wtc_code",
    "beta_list",
    "source_audio_path",
    "midi_path",
}


def main() -> None:
    df = pd.read_csv(IN_PATH, low_memory=False)

    feature_cols = [
        c
        for c in df.columns
        if c not in NON_FEATURE_COLS
        and pd.api.types.is_numeric_dtype(df[c])
        and df[c].notna().sum() >= 20
        and df[c].nunique(dropna=True) > 3
    ]
    print(f"Screening {len(feature_cols)} whole-piece/tapping features against emotion_rating_mean, n<=24 per emotion.")

    results = []
    for emotion in EMOTIONS:
        sub = df[df["emotion_term"] == emotion].copy()
        target_label = f"emotion_rating_mean__{emotion}"
        sub = sub.rename(columns={"emotion_rating_mean": target_label})
        out = base.corr_screen(sub, [target_label], feature_cols, min_n=15)
        if not out.empty:
            out.insert(0, "emotion_term", emotion)
            results.append(out)

    all_results = pd.concat(results, ignore_index=True)
    all_results.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(all_results)} rows to {OUT_PATH}")

    print("\nTop |rho| track-level (song-wide, uncorrected-for-multiple-comparisons view -- see spearman_fdr_q):")
    print(
        all_results.sort_values("abs_spearman_rho", ascending=False)
        .head(20)[["emotion_term", "feature", "spearman_rho", "spearman_p", "spearman_fdr_q", "n"]]
        .to_string(index=False)
    )

    print("\nEmotion vs. tapping coherence (istc_mean_max_unique_per_sec) specifically:")
    istc_rows = all_results[all_results["feature"] == "istc_mean_max_unique_per_sec"]
    print(istc_rows[["emotion_term", "spearman_rho", "spearman_p", "n"]].to_string(index=False))


if __name__ == "__main__":
    main()
