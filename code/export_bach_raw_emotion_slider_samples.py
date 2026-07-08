#!/usr/bin/env python3
"""Export the raw, native-resolution (250 ms) emotion-slider samples into
this repository, gzip-compressed.

Every emotion table already in this repository is a *derived* aggregate:
100 ms bin means, track-level means, or participant-trial means. This script
ships the actual per-sample data those aggregates were built from --
one row per (participant, trial, 250 ms sample) -- so this analysis can be
reproduced or re-binned at a different resolution without re-running the
PsyNet export.

De-identification: `participant_id` here is PsyNet's internal small integer
per-participant counter (not a Prolific ID, email, or other re-identifying
value) -- the same kind of identifier already used un-redacted in
`analysis__beta_sync_emotion__bach_participant_trial_level_table__redacted.csv`.
No demographic, geographic, or free-text fields are present in this export.

Adds `stim_name`, `wtc_code`, and `t_sync` (the same t=0-at-first-musical-onset
clock used everywhere else in this repository) via the stimulus crosswalk, so
the raw samples are usable directly without re-deriving the alignment -- see
`docs/emotion_integration_summary.md` for the alignment methodology.

Input (not checked into git -- see docs/data_guide.md):
  - scratch/emotion_source_data/bach_emotion_slider_main_trials_flat.csv

Output:
  - tables/analysis__beta_sync_emotion__bach_raw_emotion_slider_samples.csv.gz
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLES_PATH = REPO_ROOT / "scratch" / "emotion_source_data" / "bach_emotion_slider_main_trials_flat.csv"
CROSSWALK_PATH = REPO_ROOT / "bach_emotion_slider_id_crosswalk.csv"
OUT_PATH = REPO_ROOT / "tables" / "analysis__beta_sync_emotion__bach_raw_emotion_slider_samples.csv.gz"

# Columns dropped: none identify a person; a couple of PsyNet-internal
# bookkeeping columns are dropped as noise (constant/redundant across the
# whole export).
DROP_COLS = ["sample_response_format", "sample_scale_type"]


def main() -> None:
    samples = pd.read_csv(SAMPLES_PATH, low_memory=False)
    crosswalk = pd.read_csv(CROSSWALK_PATH)

    samples = samples[~samples["is_practice"].astype(bool)].copy()
    n_before = len(samples)
    samples = samples.merge(
        crosswalk[["stimulus_id", "stim_name", "wtc_code", "manual_onset_s"]],
        on="stimulus_id",
        how="inner",
        validate="many_to_one",
    )
    if len(samples) != n_before:
        raise SystemExit(
            f"ERROR: lost {n_before - len(samples)} sample rows joining crosswalk -- aborting."
        )
    samples["t_sync"] = samples["time_s"].astype(float) - samples["manual_onset_s"]

    samples = samples.drop(columns=[c for c in DROP_COLS if c in samples.columns])
    front_cols = [
        "participant_id",
        "trial_id",
        "stimulus_id",
        "stim_name",
        "wtc_code",
        "emotion_term",
        "time_s",
        "manual_onset_s",
        "t_sync",
        "slider_value",
    ]
    remaining = [c for c in samples.columns if c not in front_cols]
    samples = samples[front_cols + remaining]
    samples = samples.sort_values(["participant_id", "trial_id", "t_sync"])

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    samples.to_csv(OUT_PATH, index=False, compression="gzip")
    print(f"Wrote {len(samples)} rows ({samples['participant_id'].nunique()} participants, "
          f"{samples.groupby(['participant_id', 'trial_id']).ngroups} trials) to {OUT_PATH}")
    print(f"Compressed size: {OUT_PATH.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
