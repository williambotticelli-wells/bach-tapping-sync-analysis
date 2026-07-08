#!/usr/bin/env python3
"""Joint linear mixed-effects regression for local (100 ms) tapping
concentration against MIDI/acoustic features, with a random intercept per
track.

`run_bach_100ms_feature_models.py` and `run_bach_100ms_audio_feature_models.py`
already screen each MIDI/acoustic feature one at a time (within-track
centered correlation, then a closed-form Bayesian-ridge multi-feature
posterior). This script adds the piece this repo was missing relative to the
emotion-slider integration: a proper `statsmodels` MixedLM (REML) that
estimates all feature coefficients *jointly* -- controlling for collinear
features (e.g. RMS and MIDI velocity both loading on "loudness") -- while
still treating track as an explicit random-effects clustering unit rather
than a fixed-effect centering trick.

`tap_count_100ms` is treated as continuous here (same CLT-style justification
as `rating_mean` for the emotion-slider bins: counts aggregated over
~10-13 tappers per bin). See `run_bach_tapping_hierarchical_bayesian_model.py`
for the count-native (Poisson) hierarchical treatment of the same question.

Output:
  - tables/analysis__beta_sync_100ms_models__bach_100ms_tapping_mixedlm_summary.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

REPO_ROOT = Path(__file__).resolve().parents[1]
IN_PATH = REPO_ROOT / "tables" / "analysis__beta_sync_100ms__bach_100ms_audio_midi_tapping_feature_vectors.csv"
OUT_PATH = REPO_ROOT / "tables" / "analysis__beta_sync_100ms_models__bach_100ms_tapping_mixedlm_summary.csv"

FEATURES = [
    "midi_active_note_count",
    "midi_note_onset_count_100ms",
    "midi_velocity_mean",
    "midi_pitch_mean",
    "audio100_rms",
    "audio100_spectral_bandwidth_hz",
    "audio100_spectral_centroid_hz",
]


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std(ddof=1)


def main() -> None:
    df = pd.read_csv(IN_PATH, low_memory=False)
    cols = ["tap_count_100ms", "stim_name"] + FEATURES
    sub = df[cols].replace([np.inf, -np.inf], np.nan).dropna()
    for col in ["tap_count_100ms"] + FEATURES:
        sub[col] = zscore(sub[col])

    formula = "tap_count_100ms ~ " + " + ".join(FEATURES)
    model = smf.mixedlm(formula, data=sub, groups=sub["stim_name"])
    result = model.fit(reml=True, method="lbfgs")

    rows = []
    for name, coef, se, p in zip(
        result.params.index, result.params.values, result.bse.values, result.pvalues.values
    ):
        rows.append(
            {
                "level": "100ms_bin",
                "term": name,
                "coef": coef,
                "se": se,
                "p_value": p,
                "n_obs": int(result.nobs),
                "n_tracks": sub["stim_name"].nunique(),
            }
        )
    rows.append(
        {
            "level": "100ms_bin",
            "term": "group_var (stim_name random intercept variance)",
            "coef": result.cov_re.iloc[0, 0],
            "se": np.nan,
            "p_value": np.nan,
            "n_obs": int(result.nobs),
            "n_tracks": sub["stim_name"].nunique(),
        }
    )
    out = pd.DataFrame(rows)
    print(f"\n=== 100ms bin-level tapping MixedLM (n={int(result.nobs)}, tracks={sub['stim_name'].nunique()}) ===")
    print(result.summary())

    out.to_csv(OUT_PATH, index=False)
    print(f"\nWrote {len(out)} rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
