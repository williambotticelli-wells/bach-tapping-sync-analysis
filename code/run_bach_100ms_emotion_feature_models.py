#!/usr/bin/env python3
"""Run 100 ms emotion-rating feature screens, extending the existing
`run_bach_100ms_feature_models.py` methodology (within-track centering,
Spearman/Pearson correlation with BH-FDR, standardized-beta univariate OLS,
closed-form Bayesian-ridge direction screen) to the new emotion targets.

Reuses `bh_fdr`, `corr_screen`, `centered_within_track`, `ols_univariate`,
and `bayesian_ridge_multifeature` from that script verbatim (imported, not
copy-pasted) so both scripts stay numerically consistent by construction.

`rating_mean` (aggregated across ~20-30 participants per track x emotion x
bin) is treated as continuous -- justified by the central limit theorem at
that per-bin sample size -- for this exhaustive bin-level sweep. See
`build_bach_participant_trial_emotion_table.py` /
`run_bach_emotion_hierarchical_bayesian_models.py` for the ordinal treatment
of raw 1-5 responses at the participant-trial level, where the continuous
approximation is more of a stretch.

Two screens are run per emotion:
  1. Within-track (centered by stim_name, as in the base script): the local
     100 ms effect of musical/tapping features on rating, controlling for
     track-level baseline differences.
  2. Global (uncentered): included as context; can reflect track-level
     confounds, not just local dynamics (same caveat as the base script).

Outputs (in tables/, `analysis__beta_sync_emotion_models__` prefix):
  - bach_100ms_emotion_global_correlations.csv
  - bach_100ms_emotion_within_track_correlations.csv
  - bach_100ms_emotion_within_track_univariate_regressions.csv
  - bach_100ms_emotion_within_track_bayesian_ridge_screen.csv
  - bach_100ms_emotion_feature_modeling_summary.md
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "code"
IN_PATH = REPO_ROOT / "tables" / "analysis__beta_sync_emotion__bach_100ms_full_multimodal_with_emotion.csv"
OUT_DIR = REPO_ROOT / "tables"
DOCS_DIR = REPO_ROOT / "docs"
OUT_PREFIX = "analysis__beta_sync_emotion_models__"

spec = importlib.util.spec_from_file_location(
    "run_bach_100ms_feature_models", CODE_DIR / "run_bach_100ms_feature_models.py"
)
base = importlib.util.module_from_spec(spec)
sys.modules["run_bach_100ms_feature_models"] = base
spec.loader.exec_module(base)

TARGET = "rating_mean"
EMOTIONS = ["happy", "sad", "calm", "energetic"]

FEATURES_100MS = [
    "midi_note_onset_count_100ms",
    "midi_active_note_count",
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
    "tap_count_100ms",
    "audio100_rms",
    "audio100_zero_crossing_rate",
    "audio100_onset_strength_proxy",
    "audio100_spectral_centroid_hz",
    "audio100_spectral_bandwidth_hz",
    "audio100_spectral_rolloff_hz",
]


def run_for_emotion(df: pd.DataFrame, emotion: str):
    sub = df[df["emotion_term"] == emotion].copy()
    target_label = f"rating_mean__{emotion}"
    sub = sub.rename(columns={TARGET: target_label})

    global_corr = base.corr_screen(sub, [target_label], FEATURES_100MS, min_n=100)
    within = base.centered_within_track(sub, [target_label] + FEATURES_100MS)
    within_corr = base.corr_screen(within, [target_label], FEATURES_100MS, min_n=100)
    ols = base.ols_univariate(within, [target_label], FEATURES_100MS, min_n=100)
    bayes = base.bayesian_ridge_multifeature(within, target_label, FEATURES_100MS)

    for out in (global_corr, within_corr, ols, bayes):
        if not out.empty:
            out.insert(0, "emotion_term", emotion)
    return global_corr, within_corr, ols, bayes


def write_summary(within_corr: pd.DataFrame, bayes: pd.DataFrame) -> None:
    lines = [
        "# Bach 100 ms Emotion Feature Modeling Summary",
        "",
        "Screening analyses relating 100 ms MIDI/acoustic/tap-count features to",
        "aggregated emotion-slider ratings at the same 100 ms resolution, run",
        "separately per emotion category. Within-track rows are the primary",
        "local-effect screen (each track's own mean subtracted out); this",
        "controls for track-level baseline differences in both the feature and",
        "the rating, isolating local co-fluctuation.",
        "",
        "`rating_mean` here is the mean over ~20-30 participants per bin, not a",
        "raw individual response -- treated as continuous for this exhaustive",
        "bin-level sweep (justified by aggregation over many raters per cell).",
        "See the participant-trial-level hierarchical Bayesian ordinal models",
        "for analysis of the raw 1-5 responses.",
        "",
        "## 100 ms Within-Track Signals, By Emotion",
        "",
    ]
    for emotion in EMOTIONS:
        sub = within_corr[within_corr["emotion_term"] == emotion]
        if sub.empty:
            continue
        lines.append(f"### {emotion}")
        for _, row in sub.head(8).iterrows():
            lines.append(
                f"- `{row['feature']}`: Spearman rho={row['spearman_rho']:.3f}, "
                f"q={row['spearman_fdr_q']:.3g}, n={int(row['n'])}."
            )
        lines.append("")
    lines.append("## Bayesian Ridge Direction Screen, By Emotion")
    lines.append("")
    for emotion in EMOTIONS:
        sub = bayes[bayes["emotion_term"] == emotion]
        if sub.empty:
            continue
        lines.append(f"### {emotion}")
        for _, row in sub.head(8).iterrows():
            lines.append(
                f"- `{row['feature']}`: beta={row['posterior_mean_beta']:.3f}, "
                f"P(direction)={row['posterior_p_direction']:.3f}."
            )
        lines.append("")
    (DOCS_DIR / "bach_100ms_emotion_feature_modeling_summary.md").write_text(
        "\n".join(lines) + "\n"
    )


def main() -> None:
    df = pd.read_csv(IN_PATH, low_memory=False)

    global_all, within_all, ols_all, bayes_all = [], [], [], []
    for emotion in EMOTIONS:
        g, w, o, b = run_for_emotion(df, emotion)
        global_all.append(g)
        within_all.append(w)
        ols_all.append(o)
        bayes_all.append(b)

    global_corr = pd.concat([g for g in global_all if not g.empty], ignore_index=True)
    within_corr = pd.concat([w for w in within_all if not w.empty], ignore_index=True)
    ols = pd.concat([o for o in ols_all if not o.empty], ignore_index=True)
    bayes = pd.concat([b for b in bayes_all if not b.empty], ignore_index=True)

    global_corr.to_csv(OUT_DIR / f"{OUT_PREFIX}bach_100ms_emotion_global_correlations.csv", index=False)
    within_corr.to_csv(OUT_DIR / f"{OUT_PREFIX}bach_100ms_emotion_within_track_correlations.csv", index=False)
    ols.to_csv(OUT_DIR / f"{OUT_PREFIX}bach_100ms_emotion_within_track_univariate_regressions.csv", index=False)
    bayes.to_csv(OUT_DIR / f"{OUT_PREFIX}bach_100ms_emotion_within_track_bayesian_ridge_screen.csv", index=False)
    write_summary(within_corr, bayes)

    print("Top within-track correlations (|rho|), all emotions pooled:")
    print(
        within_corr.sort_values("abs_spearman_rho", ascending=False)
        .head(15)[["emotion_term", "feature", "spearman_rho", "spearman_fdr_q", "n"]]
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
