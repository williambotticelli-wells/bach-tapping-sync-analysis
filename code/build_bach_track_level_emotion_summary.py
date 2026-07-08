"""Build the track-level (song-wide, n=24 tracks x 4 emotions = 96 rows)
emotion summary and join it onto the existing whole-piece MIR/MIDI/tapping
coherence table.

Song-wide rating for a (track, emotion) cell is the mean, across
participants who rated that track under that emotion, of each participant's
own per-trial mean rating (i.e. average-of-participant-means, not a
sample-weighted average -- this avoids implicitly up-weighting participants
whose trials happen to contain more logged samples, e.g. from longer
sub-portions of a paused trial). Only post-onset samples (t_sync >= 0) are
included, consistent with the 100 ms binned table.

Inputs:
  - scratch/emotion_source_data/bach_emotion_slider_main_trials_flat.csv
  - bach_emotion_slider_id_crosswalk.csv
  - tables/analysis__beta_sync_100ms_models__bach_track_level_mir_midi_coherence_table.csv

Output:
  - tables/analysis__beta_sync_emotion__bach_track_level_emotion_tapping_mir_midi_summary.csv
    (long format: one row per stim_name x emotion_term, n=96)
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
    / "analysis__beta_sync_emotion__bach_track_level_emotion_tapping_mir_midi_summary.csv"
)


def main():
    samples = pd.read_csv(SAMPLES_PATH)
    crosswalk = pd.read_csv(CROSSWALK_PATH)
    track_level = pd.read_csv(TRACK_LEVEL_PATH)

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
    samples = samples[samples["t_sync"] >= 0]

    per_trial = (
        samples.groupby(["participant_id", "trial_id", "stim_name", "wtc_code", "emotion_term"])
        .agg(
            trial_mean_rating=("slider_value", "mean"),
            trial_sd_rating=("slider_value", "std"),
            trial_min_rating=("slider_value", "min"),
            trial_max_rating=("slider_value", "max"),
            n_samples=("slider_value", "count"),
        )
        .reset_index()
    )
    print(f"{len(per_trial)} participant-trials (post-onset samples only).")

    track_emotion = (
        per_trial.groupby(["stim_name", "wtc_code", "emotion_term"])
        .agg(
            emotion_rating_mean=("trial_mean_rating", "mean"),
            emotion_rating_sd=("trial_mean_rating", "std"),
            emotion_rating_min=("trial_mean_rating", "min"),
            emotion_rating_max=("trial_mean_rating", "max"),
            mean_within_trial_sd=("trial_sd_rating", "mean"),
            n_participants=("trial_mean_rating", "count"),
        )
        .reset_index()
    )
    track_emotion["emotion_rating_se"] = track_emotion["emotion_rating_sd"] / np.sqrt(
        track_emotion["n_participants"]
    )

    assert track_emotion["stim_name"].nunique() == 24
    assert track_emotion.groupby("stim_name").size().eq(4).all(), (
        "expected exactly 4 emotion rows per track"
    )

    merged = track_emotion.merge(track_level, on=["stim_name", "wtc_code"], how="left", validate="many_to_one")
    missing = merged[merged["istc_mean_max_unique_per_sec"].isna()]
    if len(missing):
        raise SystemExit(f"ERROR: missing track-level join for:\n{missing['stim_name'].tolist()}")

    merged = merged.sort_values(
        ["stim_name", "emotion_term"], key=lambda s: s if s.name == "emotion_term" else s.str.extract(r"(\d+)")[0].astype(int)
    )
    merged.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(merged)} rows, {len(merged.columns)} columns to {OUT_PATH}")

    summary = track_emotion.pivot(index="stim_name", columns="emotion_term", values="emotion_rating_mean")
    print("\nMean rating by track x emotion (song-wide):")
    print(summary.round(2).to_string())
    print("\nOverall mean rating by emotion (across all 24 tracks):")
    print(track_emotion.groupby("emotion_term")["emotion_rating_mean"].mean().round(3))


if __name__ == "__main__":
    main()
