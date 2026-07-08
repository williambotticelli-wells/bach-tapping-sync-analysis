"""Join the 100 ms emotion feature vectors onto the existing 100 ms
acoustic/MIDI/tapping table. Output is long-format on `emotion_term`, since
each (stim_name, bin) has up to 4 emotion rows (one per emotion category the
track was rated under) but only 1 row of shared MIDI/audio/tap features --
those get duplicated across the (up to) 4 emotion rows for that bin, which is
correct (they don't depend on emotion) and convenient for modeling with
emotion_term as a fixed effect / grouping factor.

Join key: (stim_name, wtc_code, bin_index), not bin_center_s -- the existing
`bach_100ms_midi_tapping_feature_vectors.csv` (our emotion table's grid
source) and `bach_100ms_audio_midi_tapping_feature_vectors.csv` (the combo
table we're joining onto) carry tiny floating-point drift on `bin_center_s`
(~1e-16 to ~1e-9 for a couple dozen bins out of 24,816 -- e.g. track1 bin 6:
0.6500000000000000 vs 0.6500000000000001), presumably from being written by
separately-run build scripts rather than copied verbatim. `bin_index` is an
exact integer key and is unaffected.

Inputs:
  - tables/analysis__beta_sync_100ms__bach_100ms_audio_midi_tapping_feature_vectors.csv
  - tables/analysis__beta_sync_emotion__bach_100ms_emotion_feature_vectors.csv

Output:
  - tables/analysis__beta_sync_emotion__bach_100ms_full_multimodal_with_emotion.csv
"""

import pandas as pd
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MULTIMODAL_PATH = (
    REPO_ROOT
    / "tables"
    / "analysis__beta_sync_100ms__bach_100ms_audio_midi_tapping_feature_vectors.csv"
)
EMOTION_PATH = (
    REPO_ROOT
    / "tables"
    / "analysis__beta_sync_emotion__bach_100ms_emotion_feature_vectors.csv"
)
OUT_PATH = (
    REPO_ROOT
    / "tables"
    / "analysis__beta_sync_emotion__bach_100ms_full_multimodal_with_emotion.csv"
)


def main():
    multimodal = pd.read_csv(MULTIMODAL_PATH)
    emotion = pd.read_csv(EMOTION_PATH)

    emotion_cols = [
        "stim_name",
        "wtc_code",
        "bin_index",
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
    emotion = emotion[emotion_cols].rename(
        columns={"n_participants": "n_emotion_raters"}
    )

    merged = emotion.merge(
        multimodal,
        on=["stim_name", "wtc_code", "bin_index"],
        how="left",
        validate="many_to_one",
    )

    missing = merged[merged["bin_start_s"].isna()] if "bin_start_s" in merged.columns else pd.DataFrame()
    unmatched_pct = 100 * len(missing) / len(merged) if len(merged) else 0
    print(
        f"{len(merged)} rows; {len(missing)} ({unmatched_pct:.4f}%) had no matching "
        "multimodal bin (expected only for bins beyond the multimodal table's "
        "track-length coverage, if any)."
    )

    merged = merged.sort_values(["stim_name", "emotion_term", "bin_index"])
    merged.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(merged)} rows, {len(merged.columns)} columns to {OUT_PATH}")


if __name__ == "__main__":
    main()
