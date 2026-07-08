"""Build the participant-trial-level emotion table (n ~= 2400: one row per
participant x trial). This is the unit needed for mixed-effects and
hierarchical Bayesian models with crossed random effects for track and
participant, and for the ordinal analysis of raw 1-5 responses (the 100 ms
and track-level tables only carry aggregated/continuous rating summaries).

Tapping itself was collected in a separate study with no emotion dimension,
so it cannot vary within a track here -- every participant who rated a given
track inherits the same track-level tapping/MIR/MIDI summary. This table
exists to give the *emotion x feature* relationship more statistical power
and to support individual-differences questions (e.g. does higher
within-trial rating variability relate to anything), not to claim
participant-level tapping data that doesn't exist.

Privacy: `participant_id` here is the PsyNet-internal integer id from an
export that was anonymized at export time (`--anonymize both`), not a
Prolific/worker id. No free-text or source-audio-filename fields are
included, consistent with this repo's existing `__redacted` participant-level
tables (see docs/data_guide.md).

Inputs:
  - scratch/emotion_source_data/bach_emotion_slider_main_trials_flat.csv
  - bach_emotion_slider_id_crosswalk.csv
  - tables/analysis__beta_sync_100ms_models__bach_track_level_mir_midi_coherence_table.csv

Output:
  - tables/analysis__beta_sync_emotion__bach_participant_trial_level_table__redacted.csv
"""

import numpy as np
import pandas as pd
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLES_PATH = (
    REPO_ROOT
    / "scratch"
    / "emotion_source_data"
    / "bach_emotion_slider_main_trials_flat.csv"
)
CROSSWALK_PATH = REPO_ROOT / "bach_emotion_slider_id_crosswalk.csv"
TRACK_LEVEL_PATH = (
    REPO_ROOT
    / "tables"
    / "analysis__beta_sync_100ms_models__bach_track_level_mir_midi_coherence_table.csv"
)
OUT_PATH = (
    REPO_ROOT
    / "tables"
    / "analysis__beta_sync_emotion__bach_participant_trial_level_table__redacted.csv"
)

# Track-level columns worth carrying onto each participant-trial row. We
# deliberately do NOT copy all 204 track-level columns (that would make this
# a ~2400 x 200 table for no benefit) -- just tapping coherence + a compact
# set of whole-piece MIR/MIDI summary features that are the natural targets
# for participant-trial-level modeling.
TRACK_LEVEL_FEATURE_COLS = [
    "istc_mean_max_unique_per_sec",
    "mean_tap_count_per_100ms_bin",
    "mean_unique_participants_per_100ms_bin",
    "n_participants",  # tapping-study n, renamed below to avoid clashing
    "duration_s",
    "simple_lowenergy_Mean",
    "simple_brightness_Mean",
    "simple_roughness_Mean",
    "simple_centroid_Mean",
    "rhythm_tempo_Mean",
    "dynamics_rms_Mean",
    "notedensity_per_s",
    "pitch_mean",
    "pitch_std",
    "ioi_mean_s",
    "ioi_cv",
    "beta_perf",
    "beta_score",
]


def main():
    samples = pd.read_csv(SAMPLES_PATH)
    crosswalk = pd.read_csv(CROSSWALK_PATH)
    track_level = pd.read_csv(TRACK_LEVEL_PATH)[
        ["stim_name", "wtc_code"] + TRACK_LEVEL_FEATURE_COLS
    ].rename(columns={"n_participants": "tapping_study_n_participants"})

    samples = samples[~samples["is_practice"].astype(bool)].copy()
    samples["time_s"] = samples["time_s"].astype(float)
    samples["slider_value"] = samples["slider_value"].astype(float)

    samples = samples.merge(
        crosswalk[["stimulus_id", "stim_name", "wtc_code", "manual_onset_s"]],
        on="stimulus_id",
        how="inner",
        validate="many_to_one",
    )
    samples["t_sync"] = samples["time_s"] - samples["manual_onset_s"]
    post_onset = samples[samples["t_sync"] >= 0]

    per_trial = (
        post_onset.groupby(["participant_id", "trial_id", "stim_name", "wtc_code", "emotion_term"])
        .agg(
            trial_mean_rating=("slider_value", "mean"),
            trial_sd_rating=("slider_value", "std"),
            trial_min_rating=("slider_value", "min"),
            trial_max_rating=("slider_value", "max"),
            trial_final_rating=("slider_value", "last"),
            n_samples=("slider_value", "count"),
        )
        .reset_index()
    )

    # Trial-level metadata (completion, duration, familiarity/enjoyment,
    # difficulty) is constant within a trial -- take the last logged row.
    meta_cols = [
        "participant_id",
        "trial_id",
        "completed_audio",
        "audio_duration_s",
        "response_duration_s",
        "missed_sample_count",
        "familiarity",
        "enjoyment",
        "playback_difficulty",
    ]
    trial_meta = samples.sort_values("sample_index").groupby(
        ["participant_id", "trial_id"]
    )[meta_cols[2:]].last().reset_index()

    per_trial = per_trial.merge(trial_meta, on=["participant_id", "trial_id"], how="left")

    # Trial order within participant (fatigue / order-effect covariate).
    per_trial["trial_order"] = per_trial.groupby("participant_id")["trial_id"].rank(method="first")

    merged = per_trial.merge(track_level, on=["stim_name", "wtc_code"], how="left", validate="many_to_one")
    missing = merged[merged["istc_mean_max_unique_per_sec"].isna()]
    if len(missing):
        raise SystemExit(f"ERROR: missing track-level join for stim_names:\n{missing['stim_name'].unique()}")

    n_expected = 201 * 12
    print(
        f"{len(merged)} participant-trial rows (expect ~{n_expected} if all "
        "201 approved x 12 trials; slightly fewer if some non-approved "
        "participants had incomplete trials, slightly more if working/"
        "returned participants completed some trials before export)."
    )

    merged = merged.sort_values(["participant_id", "trial_order"]).reset_index(drop=True)
    merged.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(merged)} rows, {len(merged.columns)} columns to {OUT_PATH}")
    print(f"\nParticipants: {merged['participant_id'].nunique()}")
    print(f"Emotion counts (trials): \n{merged['emotion_term'].value_counts()}")
    print(f"\nEmotion counts (unique participants): \n{merged.groupby('emotion_term')['participant_id'].nunique()}")


if __name__ == "__main__":
    main()
