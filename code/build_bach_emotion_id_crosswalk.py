"""Build the bach_XX <-> track_N id crosswalk needed to join the continuous
emotion-slider experiment (PsyNet, stimulus ids bach_01..bach_24) onto the
existing tapping/MIR/MIDI sync-analysis tables (stim_name track1..track24).

Match key: exact `oname` (original WAV basename). The slider manifest and the
sync manifest were each independently corrected for the wtc1f03/wtc1p03
" 2"-suffix ambiguity (see docs/data_guide.md and the parent repo's
next-bach-steps-md/bach-project-audit-2026-06-30.md); this script re-derives
the join from the corrected files rather than hard-coding the mapping, so it
stays correct if either manifest changes.

Also carries over `manual_onset_s` (per-track, first-musical-onset t=0 crop
point) from the sync manifest, since the emotion slider's `time_s` is
wall-clock-from-playback-start and must be corrected by this value before
joining onto any `bin_center_s` / `window_center_s` grid.

Inputs:
  - continuous_emotion_slider_experiment/manifests/bach_24_stimulus_manifest.csv
  - tables/bach_beta_midi_sync_manifest.csv

Output:
  - bach_emotion_slider_id_crosswalk.csv (repo root, alongside
    bach_beta_midi_sync_manifest.csv / piece_mapping_notes.csv)
"""

import pandas as pd
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACH_SUBREPO_ROOT = REPO_ROOT.parent

SLIDER_MANIFEST = (
    BACH_SUBREPO_ROOT
    / "continuous_emotion_slider_experiment"
    / "manifests"
    / "bach_24_stimulus_manifest.csv"
)
SYNC_MANIFEST = REPO_ROOT / "tables" / "bach_beta_midi_sync_manifest.csv"
OUT_PATH = REPO_ROOT / "bach_emotion_slider_id_crosswalk.csv"

# track8/track9/track10/track23 all reuse an oname that collides across two
# *physically different* recordings (a long wtc1f03 performance and a short
# wtc1p03 performance sharing a base filename once the slider-side " 2"
# duplicate-disambiguation suffix is stripped -- see
# bach-project-audit-2026-06-30.md, "Continuous Slider Experiment Audit",
# 2026-07-02 update). That audit independently re-derived this exact mapping
# via real audio duration (`afinfo`) and aligned-MIDI-onset cross-checks
# against the sync manifest's own settled wtc_code per track (long ~131-150s
# -> wtc1f03 -> track8/track9; short ~74-83s -> wtc1p03 -> track10/track23),
# and it matches piece_mapping_notes.csv's independently-recorded resolution.
# Not derivable from `oname` text alone, so it is hard-coded here rather than
# silently guessed.
AMBIGUOUS_ONAME_OVERRIDES = {
    "bach_17": "track9",  # wtc1f03, long (~150s)
    "bach_18": "track8",  # wtc1f03, long (~131s)
    "bach_21": "track10",  # wtc1p03, short (~83s)
    "bach_22": "track23",  # wtc1p03, short (~74s)
}


def main():
    slider = pd.read_csv(SLIDER_MANIFEST)
    sync = pd.read_csv(SYNC_MANIFEST)

    slider = slider[["stimulus_id", "piece", "oname"]].rename(
        columns={"piece": "slider_wtc_code"}
    )
    sync_cols = sync[
        [
            "stim_name",
            "wtc_code",
            "manifest_wtc_code",
            "beta_piece_override_applied",
            "deployed_basename_normalized",
            "manual_onset_s",
            "onset_source",
            "sync_status",
        ]
    ].rename(columns={"deployed_basename_normalized": "oname"})

    ambiguous_ids = set(AMBIGUOUS_ONAME_OVERRIDES)
    unambiguous = slider[~slider["stimulus_id"].isin(ambiguous_ids)]
    ambiguous = slider[slider["stimulus_id"].isin(ambiguous_ids)]

    dup_onames = sync_cols["oname"].value_counts()
    dup_onames = set(dup_onames[dup_onames > 1].index)
    still_ambiguous = unambiguous[unambiguous["oname"].isin(dup_onames)]
    if len(still_ambiguous):
        raise SystemExit(
            "ERROR: found an oname collision that isn't in "
            f"AMBIGUOUS_ONAME_OVERRIDES -- crosswalk logic is stale:\n"
            f"{still_ambiguous.to_string(index=False)}"
        )

    sync_cols_unambiguous = sync_cols[~sync_cols["oname"].isin(dup_onames)]
    merged_auto = unambiguous.merge(
        sync_cols_unambiguous, on="oname", how="left", validate="one_to_one"
    )
    missing = merged_auto[merged_auto["stim_name"].isna()]
    if len(missing):
        raise SystemExit(
            "ERROR: the following slider stimuli did not find an exact `oname` "
            f"match in the sync manifest -- crosswalk is NOT trustworthy until "
            f"this is resolved:\n{missing[['stimulus_id', 'oname']].to_string(index=False)}"
        )

    ambiguous = ambiguous.copy()
    ambiguous["stim_name"] = ambiguous["stimulus_id"].map(AMBIGUOUS_ONAME_OVERRIDES)
    sync_lookup = sync_cols.set_index("stim_name")
    for col in [
        "wtc_code",
        "manifest_wtc_code",
        "beta_piece_override_applied",
        "manual_onset_s",
        "onset_source",
        "sync_status",
    ]:
        ambiguous[col] = ambiguous["stim_name"].map(sync_lookup[col])

    merged = pd.concat([merged_auto, ambiguous], ignore_index=True)

    mismatched_wtc = merged[merged["slider_wtc_code"] != merged["wtc_code"]]
    if len(mismatched_wtc):
        print(
            "NOTE: the following stimuli have a slider-side WTC code that differs "
            "from the sync manifest's (post-override) WTC code -- expected for "
            "the track8/9/10/23 group (BETA_PIECE_OVERRIDES applied on the sync "
            "side; slider side kept the pre-override source-table label) and is "
            "not an error:"
        )
        print(
            mismatched_wtc[
                ["stimulus_id", "stim_name", "slider_wtc_code", "wtc_code"]
            ].to_string(index=False)
        )

    assert merged["stim_name"].nunique() == 24, "expected exactly 24 unique tracks"
    assert merged["stimulus_id"].nunique() == 24, "expected exactly 24 unique stimuli"
    assert not merged["manual_onset_s"].isna().any(), "missing manual_onset_s for some track"

    merged = merged.sort_values(
        "stimulus_id", key=lambda s: s.str.extract(r"(\d+)")[0].astype(int)
    ).reset_index(drop=True)
    merged.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(merged)} rows to {OUT_PATH}")
    print(merged.to_string(index=False))


if __name__ == "__main__":
    main()
