"""Resample the continuous emotion-slider trajectories onto the same 100 ms
grid (`bin_center_s`) used by the MIDI/audio/tapping tables, and aggregate
across participants to produce per-(stim_name, wtc_code, emotion_term,
bin_center_s) rating summaries.

Time alignment: the slider records `time_s` as wall-clock-from-playback-start
(`promptStart`), while every downstream sync-analysis table uses `t=0` =
first musical onset (`manual_onset_s` per track, from
`tables/bach_beta_midi_sync_manifest.csv`). We compute
`t_sync = time_s - manual_onset_s` per track before binning (see
bach-project-audit-2026-06-30.md and docs/data_guide.md).

Resampling: the slider is a `likert_5` push-button control sampled every
250 ms, i.e. coarser than the 100 ms target grid, and its value only changes
on a button press (a step function, not a continuous signal). We therefore
use last-observation-carried-forward ("asof backward") rather than
interpolation to assign each 100 ms bin the value the participant's slider
actually displayed at that instant, rather than inventing intermediate
values between button presses. Backward-asof intentionally allows matching
against samples recorded *before* t_sync = 0 (i.e. before the first musical
onset, while the participant is looking at/adjusting the still-silent
slider), since that's the participant's real state at bin 0; only the output
*bins* are restricted to bin_start_s >= 0 (no bin exists before the musical
onset in the MIR/MIDI/tapping tables either).

Output grid is taken directly from the checked-in 100 ms MIDI table
(`bin_index`, `bin_start_s`, `bin_end_s`, `bin_center_s`) per `stim_name`, so
`bin_center_s` values are guaranteed to match exactly (no floating-point
drift from independently re-deriving the grid).

Inputs:
  - scratch/emotion_source_data/bach_emotion_slider_main_trials_flat.csv
    (flattened PsyNet export; NOT checked into git -- raw per-sample,
    per-participant data)
  - bach_emotion_slider_id_crosswalk.csv
  - tables/analysis__beta_sync_100ms__bach_100ms_midi_tapping_feature_vectors.csv
    (used only for its bin grid)

Outputs:
  - tables/analysis__beta_sync_emotion__bach_100ms_emotion_feature_vectors.csv
    (aggregated across participants -- no participant identifiers)
  - tables/analysis__beta_sync_emotion__bach_100ms_emotion_feature_vector_inventory.csv
    (small column/coverage summary, mirrors bach_100ms_feature_vector_inventory.csv)
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
GRID_SOURCE_PATH = (
    REPO_ROOT
    / "tables"
    / "analysis__beta_sync_100ms__bach_100ms_midi_tapping_feature_vectors.csv"
)
OUT_TABLE = (
    REPO_ROOT
    / "tables"
    / "analysis__beta_sync_emotion__bach_100ms_emotion_feature_vectors.csv"
)
OUT_INVENTORY = (
    REPO_ROOT
    / "tables"
    / "analysis__beta_sync_emotion__bach_100ms_emotion_feature_vector_inventory.csv"
)

BIN_WIDTH_S = 0.1


def main():
    samples = pd.read_csv(SAMPLES_PATH)
    crosswalk = pd.read_csv(CROSSWALK_PATH)
    grid = pd.read_csv(
        GRID_SOURCE_PATH,
        usecols=["stim_name", "wtc_code", "bin_index", "bin_start_s", "bin_end_s", "bin_center_s"],
    ).drop_duplicates()

    samples = samples[~samples["is_practice"].astype(bool)].copy()
    samples["time_s"] = samples["time_s"].astype(float)
    samples["slider_value"] = samples["slider_value"].astype(float)

    n_before = len(samples)
    samples = samples.merge(
        crosswalk[["stimulus_id", "stim_name", "wtc_code", "manual_onset_s"]],
        on="stimulus_id",
        how="inner",
        validate="many_to_one",
    )
    if len(samples) != n_before:
        raise SystemExit(
            f"ERROR: lost {n_before - len(samples)} sample rows joining crosswalk "
            "-- some stimulus_id was not in the crosswalk. Aborting."
        )

    samples["t_sync"] = samples["time_s"] - samples["manual_onset_s"]
    samples = samples.sort_values(["participant_id", "trial_id", "t_sync"])

    n_trials = samples.groupby(["participant_id", "trial_id"]).ngroups
    print(f"Loaded {len(samples)} main-trial samples across {n_trials} participant-trials.")

    # Expand the bin grid per stim_name into one row per (participant_id,
    # trial_id, bin), carrying along the trial's emotion_term for the final
    # aggregation. merge_asof requires numeric sort keys and a `by` group.
    trial_meta = (
        samples[["participant_id", "trial_id", "stim_name", "wtc_code", "emotion_term"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    bins_expanded = trial_meta.merge(grid, on=["stim_name", "wtc_code"], how="left")
    missing_grid = bins_expanded[bins_expanded["bin_index"].isna()]
    if len(missing_grid):
        raise SystemExit(
            "ERROR: no 100ms grid found for some (stim_name, wtc_code) pairs:\n"
            f"{missing_grid[['stim_name', 'wtc_code']].drop_duplicates().to_string(index=False)}"
        )

    # merge_asof with `by=` still requires each frame globally sorted by its
    # `on` key (not just sorted within each by-group).
    bins_expanded = bins_expanded.sort_values("bin_center_s")
    samples_for_asof = samples[
        ["participant_id", "trial_id", "t_sync", "slider_value"]
    ].sort_values("t_sync")

    matched = pd.merge_asof(
        bins_expanded,
        samples_for_asof,
        left_on="bin_center_s",
        right_on="t_sync",
        by=["participant_id", "trial_id"],
        direction="backward",
    )

    n_unmatched = matched["slider_value"].isna().sum()
    if n_unmatched:
        # Bins earlier than a trial's first recorded sample (should be rare --
        # only possible if the very first sample was recorded strictly after
        # t_sync=0, which would mean the participant hadn't seen any part of
        # the piece yet). Forward-fill within trial as the least-bad fallback
        # and flag prominently rather than silently dropping.
        pct = 100 * n_unmatched / len(matched)
        print(
            f"WARNING: {n_unmatched} / {len(matched)} bins ({pct:.4f}%) had no "
            "backward sample match (bin earlier than trial's first recorded "
            "sample); forward-filling within trial as fallback."
        )
        matched["slider_value"] = matched.groupby(["participant_id", "trial_id"])[
            "slider_value"
        ].bfill()
        still_missing = matched["slider_value"].isna().sum()
        if still_missing:
            print(
                f"WARNING: {still_missing} bins still missing after fallback "
                "(entire trial had no valid samples?); these rows are dropped."
            )
            matched = matched.dropna(subset=["slider_value"])

    matched = matched[matched["bin_start_s"] >= 0].copy()

    agg = (
        matched.groupby(["stim_name", "wtc_code", "emotion_term", "bin_index"])
        .agg(
            bin_start_s=("bin_start_s", "first"),
            bin_end_s=("bin_end_s", "first"),
            bin_center_s=("bin_center_s", "first"),
            rating_mean=("slider_value", "mean"),
            rating_sd=("slider_value", "std"),
            n_ratings=("slider_value", "count"),
            n_participants=("participant_id", "nunique"),
        )
        .reset_index()
    )
    agg["bin_width_s"] = BIN_WIDTH_S
    agg["rating_se"] = agg["rating_sd"] / np.sqrt(agg["n_participants"])
    agg["response_format"] = "likert_5"
    agg["scale_min"] = 1
    agg["scale_max"] = 5

    agg = agg[
        [
            "stim_name",
            "wtc_code",
            "bin_index",
            "bin_start_s",
            "bin_end_s",
            "bin_center_s",
            "bin_width_s",
            "emotion_term",
            "rating_mean",
            "rating_sd",
            "rating_se",
            "n_ratings",
            "n_participants",
            "response_format",
            "scale_min",
            "scale_max",
        ]
    ].sort_values(["stim_name", "emotion_term", "bin_index"])

    agg.to_csv(OUT_TABLE, index=False)
    print(f"Wrote {len(agg)} rows to {OUT_TABLE}")

    inventory_rows = []
    for track in sorted(agg["stim_name"].unique(), key=lambda s: int(s.replace("track", ""))):
        sub = agg[agg["stim_name"] == track]
        for emo in sorted(sub["emotion_term"].unique()):
            emo_sub = sub[sub["emotion_term"] == emo]
            inventory_rows.append(
                {
                    "stim_name": track,
                    "emotion_term": emo,
                    "n_bins": len(emo_sub),
                    "min_n_participants": emo_sub["n_participants"].min(),
                    "max_n_participants": emo_sub["n_participants"].max(),
                    "mean_n_participants": round(emo_sub["n_participants"].mean(), 2),
                }
            )
    inventory = pd.DataFrame(inventory_rows)
    inventory.to_csv(OUT_INVENTORY, index=False)
    print(f"Wrote {len(inventory)} rows to {OUT_INVENTORY}")
    print(inventory.to_string(index=False))


if __name__ == "__main__":
    main()
