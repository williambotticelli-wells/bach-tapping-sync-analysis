#!/usr/bin/env python3
"""Build 100 ms MIDI/tapping feature vectors for Bach analyses.

The output is intended for joining with emotion/ECoG time series. It uses the
same first-musical-onset clock as the beta-sync manifest.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
BACH_ROOT = SCRIPT_DIR.parents[0]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compute_bach_tap_metrics import taps_from_row  # noqa: E402


MANIFEST = BACH_ROOT / "alignment" / "beta_midi_sync_draft" / "bach_beta_midi_sync_manifest.csv"
MIDI_EVENTS = BACH_ROOT / "analysis" / "beta_sync_features" / "midi_note_events_aligned.csv"
TAP_INPUT = (
    BACH_ROOT
    / "bach-tap-data/bach-tap/bach-tapping/bach-tapping-data/database/derived/"
    "tap_all_trials_combined_usable.csv"
)
OUT_DIR = BACH_ROOT / "analysis" / "beta_sync_100ms"
BIN_S = 0.100


def load_taps(manifest: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(TAP_INPUT, low_memory=False)
    if "usable" in df.columns:
        df = df[df["usable"].fillna(False).astype(bool)].copy()
    offsets = dict(
        zip(
            manifest["stim_name"],
            pd.to_numeric(manifest["manual_onset_s"], errors="coerce").fillna(0.0),
        )
    )
    rows = []
    for _, row in df.iterrows():
        stim = str(row.get("stim_name", ""))
        offset = float(offsets.get(stim, 0.0))
        taps = taps_from_row(row) - offset
        taps = taps[np.isfinite(taps)]
        taps = taps[taps >= 0]
        participant = str(row.get("participant_uid", row.get("participant_id", "")))
        for tap in taps:
            rows.append({"stim_name": stim, "participant_key": participant, "tap_time_s": float(tap)})
    return pd.DataFrame(rows)


def summarize_midi(notes: pd.DataFrame, bin_start: float, bin_end: float) -> dict[str, float]:
    onset_mask = (notes["note_start_s_aligned"] >= bin_start) & (notes["note_start_s_aligned"] < bin_end)
    active_mask = (notes["note_start_s_aligned"] < bin_end) & (notes["note_end_s_aligned"] > bin_start)
    onset_notes = notes[onset_mask]
    active_notes = notes[active_mask]
    pitch_series = active_notes["pitch"] if not active_notes.empty else onset_notes["pitch"]
    velocity_series = active_notes["velocity"] if not active_notes.empty else onset_notes["velocity"]
    out = {
        "midi_note_onset_count_100ms": int(len(onset_notes)),
        "midi_note_onset_density_per_s": float(len(onset_notes) / BIN_S),
        "midi_active_note_count": int(len(active_notes)),
        "midi_active_note_density_per_s": float(len(active_notes) / BIN_S),
        "midi_pitch_min": np.nan,
        "midi_pitch_max": np.nan,
        "midi_pitch_range": np.nan,
        "midi_pitch_mean": np.nan,
        "midi_pitch_std": np.nan,
        "midi_velocity_min": np.nan,
        "midi_velocity_max": np.nan,
        "midi_velocity_range": np.nan,
        "midi_velocity_mean": np.nan,
        "midi_velocity_std": np.nan,
        "midi_dynamic_range": np.nan,
    }
    if len(pitch_series):
        pitches = pd.to_numeric(pitch_series, errors="coerce").dropna()
        if len(pitches):
            out.update(
                {
                    "midi_pitch_min": float(pitches.min()),
                    "midi_pitch_max": float(pitches.max()),
                    "midi_pitch_range": float(pitches.max() - pitches.min()),
                    "midi_pitch_mean": float(pitches.mean()),
                    "midi_pitch_std": float(pitches.std(ddof=1)) if len(pitches) > 1 else 0.0,
                }
            )
    if len(velocity_series):
        velocities = pd.to_numeric(velocity_series, errors="coerce").dropna()
        if len(velocities):
            v_range = float(velocities.max() - velocities.min())
            out.update(
                {
                    "midi_velocity_min": float(velocities.min()),
                    "midi_velocity_max": float(velocities.max()),
                    "midi_velocity_range": v_range,
                    "midi_velocity_mean": float(velocities.mean()),
                    "midi_velocity_std": float(velocities.std(ddof=1)) if len(velocities) > 1 else 0.0,
                    "midi_dynamic_range": v_range,
                }
            )
    return out


def summarize_taps(taps: pd.DataFrame, bin_start: float, bin_end: float) -> dict[str, float]:
    if taps.empty:
        return {
            "tap_count_100ms": 0,
            "unique_tapper_count_100ms": 0,
            "tap_density_per_s": 0.0,
        }
    sub = taps[(taps["tap_time_s"] >= bin_start) & (taps["tap_time_s"] < bin_end)]
    return {
        "tap_count_100ms": int(len(sub)),
        "unique_tapper_count_100ms": int(sub["participant_key"].nunique()) if not sub.empty else 0,
        "tap_density_per_s": float(len(sub) / BIN_S),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(MANIFEST, dtype=str).fillna("")
    midi = pd.read_csv(MIDI_EVENTS, low_memory=False)
    taps = load_taps(manifest)
    rows = []
    inventory_rows = []
    for _, meta in manifest.iterrows():
        stim = meta["stim_name"]
        wtc = meta["wtc_code"]
        duration = float(pd.to_numeric(pd.Series([meta.get("deployed_t0_duration_s", "")]), errors="coerce").fillna(0.0).iloc[0])
        notes = midi[midi["stim_name"].astype(str) == stim].copy()
        tap_sub = taps[taps["stim_name"] == stim].copy() if not taps.empty else pd.DataFrame()
        n_bins = int(np.ceil(duration / BIN_S)) if duration > 0 else 0
        for idx in range(n_bins):
            start = round(idx * BIN_S, 10)
            end = min(duration, start + BIN_S)
            center = (start + end) / 2.0
            row = {
                "stim_name": stim,
                "wtc_code": wtc,
                "bin_index": idx,
                "bin_start_s": start,
                "bin_end_s": end,
                "bin_center_s": center,
                "bin_width_s": end - start,
            }
            row.update(summarize_midi(notes, start, end))
            row.update(summarize_taps(tap_sub, start, end))
            rows.append(row)
        inventory_rows.append(
            {
                "stim_name": stim,
                "wtc_code": wtc,
                "duration_s": duration,
                "n_100ms_bins": n_bins,
                "n_midi_notes": int(len(notes)),
                "n_taps": int(len(tap_sub)) if not tap_sub.empty else 0,
                "n_tappers": int(tap_sub["participant_key"].nunique()) if not tap_sub.empty else 0,
            }
        )
    out = pd.DataFrame(rows)
    inventory = pd.DataFrame(inventory_rows)
    out.to_csv(OUT_DIR / "bach_100ms_midi_tapping_feature_vectors.csv", index=False)
    inventory.to_csv(OUT_DIR / "bach_100ms_feature_vector_inventory.csv", index=False)
    (OUT_DIR / "README.md").write_text(
        "# Bach 100 ms MIDI + Tapping Feature Vectors\n\n"
        "These tables use the beta-sync first-musical-onset timebase (`t=0`).\n\n"
        "- `bach_100ms_midi_tapping_feature_vectors.csv`: one row per 100 ms bin.\n"
        "- `bach_100ms_feature_vector_inventory.csv`: per-track row counts and coverage.\n\n"
        "MIDI features include note onset density, active note count, pitch min/max/range,\n"
        "and velocity/dynamic range. Tapping features include total tap count and unique\n"
        "tapper count per 100 ms bin.\n",
        encoding="utf-8",
    )
    print(OUT_DIR / "bach_100ms_midi_tapping_feature_vectors.csv")
    print(f"rows={len(out)} tracks={out['stim_name'].nunique() if not out.empty else 0}")


if __name__ == "__main__":
    main()
