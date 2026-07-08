#!/usr/bin/env python3
"""Linear mixed-effects regressions for the emotion-slider data, at two
levels:

1. 100 ms bin level (n ~= 99k rows): rating_mean ~ standardized features,
   with a random intercept for stim_name (track), fit separately per
   emotion. This is the appropriate step beyond the univariate
   within-track-centered OLS in run_bach_100ms_emotion_feature_models.py --
   it estimates all feature coefficients *jointly* (controlling for
   collinear features, e.g. RMS and velocity both loading on "loudness")
   rather than one at a time, while still accounting for track as a
   clustering unit.

2. Participant-trial level (n ~= 2400 rows): trial_mean_rating ~ tapping
   coherence + whole-piece MIR/MIDI features + emotion fixed effect, with
   crossed random intercepts for stim_name (track) and participant_id. This
   is the appropriate level for testing whether track-level tapping
   coherence relates to how a track is rated, now with participant-level
   power (n~2400) instead of track-level power (n=24) -- while still being
   honest that tapping coherence itself only has 24 unique values (one per
   track), so its standard error is fundamentally limited by the n=24
   between-track variation, not the n=2400 row count.

Uses statsmodels MixedLM (REML). All continuous predictors are
z-standardized within the fitted sample so coefficients are directly
comparable in magnitude.

Outputs:
  - tables/analysis__beta_sync_emotion_models__bach_100ms_emotion_mixedlm_summary.csv
  - tables/analysis__beta_sync_emotion_models__bach_participant_trial_emotion_mixedlm_summary.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

REPO_ROOT = Path(__file__).resolve().parents[1]
BIN_LEVEL_PATH = REPO_ROOT / "tables" / "analysis__beta_sync_emotion__bach_100ms_full_multimodal_with_emotion.csv"
TRIAL_LEVEL_PATH = REPO_ROOT / "tables" / "analysis__beta_sync_emotion__bach_participant_trial_level_table__redacted.csv"
OUT_BIN = REPO_ROOT / "tables" / "analysis__beta_sync_emotion_models__bach_100ms_emotion_mixedlm_summary.csv"
OUT_TRIAL = REPO_ROOT / "tables" / "analysis__beta_sync_emotion_models__bach_participant_trial_emotion_mixedlm_summary.csv"

EMOTIONS = ["happy", "sad", "calm", "energetic"]

BIN_FEATURES = [
    "midi_active_note_count",
    "midi_velocity_mean",
    "midi_pitch_mean",
    "audio100_rms",
    "audio100_spectral_centroid_hz",
    "audio100_spectral_bandwidth_hz",
    "tap_count_100ms",
]

TRIAL_FEATURES = [
    "istc_mean_max_unique_per_sec",
    "notedensity_per_s",
    "pitch_mean",
    "rhythm_tempo_Mean",
    "dynamics_rms_Mean",
    "simple_brightness_Mean",
]


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std(ddof=1)


def fit_bin_level_mixedlm() -> pd.DataFrame:
    df = pd.read_csv(BIN_LEVEL_PATH, low_memory=False)
    rows = []
    for emotion in EMOTIONS:
        sub = df[df["emotion_term"] == emotion].copy()
        cols = ["rating_mean", "stim_name"] + BIN_FEATURES
        sub = sub[cols].replace([np.inf, -np.inf], np.nan).dropna()
        for col in ["rating_mean"] + BIN_FEATURES:
            sub[col] = zscore(sub[col])
        formula = "rating_mean ~ " + " + ".join(BIN_FEATURES)
        model = smf.mixedlm(formula, data=sub, groups=sub["stim_name"])
        result = model.fit(reml=True, method="lbfgs")
        for name, coef, se, p in zip(
            result.params.index, result.params.values, result.bse.values, result.pvalues.values
        ):
            rows.append(
                {
                    "level": "100ms_bin",
                    "emotion_term": emotion,
                    "term": name,
                    "coef": coef,
                    "se": se,
                    "p_value": p,
                    "n_obs": int(result.nobs),
                    "n_groups": sub["stim_name"].nunique(),
                }
            )
        rows.append(
            {
                "level": "100ms_bin",
                "emotion_term": emotion,
                "term": "group_var (stim_name random intercept variance)",
                "coef": result.cov_re.iloc[0, 0],
                "se": np.nan,
                "p_value": np.nan,
                "n_obs": int(result.nobs),
                "n_groups": sub["stim_name"].nunique(),
            }
        )
        print(f"\n=== 100ms bin-level MixedLM: {emotion} (n={int(result.nobs)}) ===")
        print(result.summary())
    return pd.DataFrame(rows)


def fit_trial_level_mixedlm() -> pd.DataFrame:
    df = pd.read_csv(TRIAL_LEVEL_PATH, low_memory=False)
    df = df[df["completed_audio"] == True].copy()  # noqa: E712

    cols = ["trial_mean_rating", "stim_name", "participant_id", "emotion_term"] + TRIAL_FEATURES
    sub = df[cols].replace([np.inf, -np.inf], np.nan).dropna()
    for col in ["trial_mean_rating"] + TRIAL_FEATURES:
        sub[col] = zscore(sub[col])
    sub["emotion_term"] = pd.Categorical(sub["emotion_term"], categories=EMOTIONS)

    formula = "trial_mean_rating ~ " + " + ".join(TRIAL_FEATURES) + " + C(emotion_term)"
    # Crossed random effects (track + participant) aren't natively supported
    # by a single MixedLM call; approximate with participant as the primary
    # grouping factor (repeated observations per participant across their 12
    # trials) and stim_name as a variance-component (vc_formula), which
    # statsmodels does support for a limited crossed-effects case.
    vc = {"stim_name": "0 + C(stim_name)"}
    model = smf.mixedlm(
        formula, data=sub, groups=sub["participant_id"], vc_formula=vc
    )
    result = model.fit(reml=True, method="lbfgs")

    rows = []
    for name, coef, se, p in zip(
        result.params.index, result.params.values, result.bse.values, result.pvalues.values
    ):
        rows.append(
            {
                "level": "participant_trial",
                "term": name,
                "coef": coef,
                "se": se,
                "p_value": p,
                "n_obs": int(result.nobs),
                "n_participants": sub["participant_id"].nunique(),
                "n_tracks": sub["stim_name"].nunique(),
            }
        )
    print(f"\n=== Participant-trial-level MixedLM (n={int(result.nobs)}, participants={sub['participant_id'].nunique()}, tracks={sub['stim_name'].nunique()}) ===")
    print(result.summary())
    return pd.DataFrame(rows)


def main() -> None:
    bin_results = fit_bin_level_mixedlm()
    bin_results.to_csv(OUT_BIN, index=False)
    print(f"\nWrote {len(bin_results)} rows to {OUT_BIN}")

    trial_results = fit_trial_level_mixedlm()
    trial_results.to_csv(OUT_TRIAL, index=False)
    print(f"Wrote {len(trial_results)} rows to {OUT_TRIAL}")


if __name__ == "__main__":
    main()
