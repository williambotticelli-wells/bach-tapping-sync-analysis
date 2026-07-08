#!/usr/bin/env python3
"""Export raw (de-identified) tap-event timestamps per trial.

Every tapping table already in this repository is a *derived* summary
(inter-onset-interval statistics, ISTC coherence, KDE consensus peaks) --
useful for feature/coherence screens, but not reproducible from scratch
without the underlying tap-time arrays. This script exports those raw
arrays directly, using the exact same redaction convention already applied
to `analysis__beta_sync_tapping__trial_ioi_metrics__redacted.csv` and
`..._ioi_ratio_per_trial__redacted.csv` (see the collaborator-package build
script in the full workspace): `participant_uid`/`participant_id`/
`audio_filename` are dropped, and `trial_row` (the row's position in the raw
PsyNet/REPP export, not a participant identifier) is the only per-trial key,
so results here join directly onto those two existing redacted tables.

Tap times are on the stimulus-relative `t=0`-at-first-onset clock used
everywhere else in this repository (`manual_onset_s` subtracted from the
REPP response-clock tap times, per `bach_beta_midi_sync_manifest.csv`) --
NOT the raw REPP response clock.

Must be run from the full Bach workspace layout (needs
`bach-tap-data/bach-tap/bach-tapping/bach-tapping-data/database/derived/
tap_all_trials_combined.csv`, which is not part of this collaborator
package); the output CSV it produces is what is checked into `tables/`.

Output:
  - tables/analysis__beta_sync_tapping__raw_tap_events_per_trial__redacted.csv
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = REPO_ROOT.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from compute_bach_tap_metrics import row_offset_s, taps_from_row  # noqa: E402

RAW_INPUT = (
    WORKSPACE_ROOT
    / "bach-tap-data/bach-tap/bach-tapping/bach-tapping-data/database/derived/"
    "tap_all_trials_combined_usable.csv"
)
SYNC_MANIFEST = REPO_ROOT / "tables" / "bach_beta_midi_sync_manifest.csv"
OUT_PATH = (
    REPO_ROOT
    / "tables"
    / "analysis__beta_sync_tapping__raw_tap_events_per_trial__redacted.csv"
)


def main() -> None:
    if not RAW_INPUT.exists():
        raise SystemExit(
            f"Raw tapping export not found at {RAW_INPUT} -- this script must be "
            "run from the full Bach workspace layout, not this collaborator package."
        )

    df = pd.read_csv(RAW_INPUT, low_memory=False)
    if "usable" in df.columns:
        df = df[df["usable"].fillna(False).astype(bool)].copy()
    elif "failed" in df.columns:
        df = df[~df["failed"].fillna(False).astype(bool)].copy()

    manifest = pd.read_csv(SYNC_MANIFEST, low_memory=False)
    offsets = dict(
        zip(manifest["stim_name"], pd.to_numeric(manifest["manual_onset_s"], errors="coerce").fillna(0.0))
    )

    rows = []
    for idx, row in df.iterrows():
        stim = str(row.get("stim_name", row.get("audio_filename", "unknown")))
        offset_s = row_offset_s(row, offsets)
        taps = taps_from_row(row) - offset_s
        rows.append(
            {
                "trial_row": idx,
                "stim_name": stim,
                "alignment_offset_s": offset_s,
                "usable": row.get("usable", not bool(row.get("failed", False))),
                "n_taps": int(taps.size),
                "taps_s": json.dumps([round(float(t), 4) for t in taps]),
            }
        )
    out = pd.DataFrame(rows)

    meta_cols = ["stim_name", "wtc_code", "manifest_wtc_code", "beta_list", "beta_perf", "beta_score"]
    meta = manifest[[c for c in meta_cols if c in manifest.columns]].drop_duplicates("stim_name")
    out = out.merge(meta, on="stim_name", how="left")

    out.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(out)} trials ({out['n_taps'].sum()} total tap events) to {OUT_PATH}")
    print(f"Tracks covered: {out['stim_name'].nunique()}")


if __name__ == "__main__":
    main()
