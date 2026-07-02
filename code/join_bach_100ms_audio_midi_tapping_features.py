#!/usr/bin/env python3
"""Join 100 ms Bach audio/MIR, MIDI, and tapping feature vectors."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


BACH_ROOT = Path(__file__).resolve().parents[1]
BASE_100MS = BACH_ROOT / "analysis" / "beta_sync_100ms" / "bach_100ms_midi_tapping_feature_vectors.csv"
PY_AUDIO_100MS = BACH_ROOT / "analysis" / "beta_sync_100ms" / "bach_100ms_audio_feature_vectors.csv"
MIRTOOLBOX_100MS = BACH_ROOT / "analysis" / "matlab_toolbox_features" / "mirtoolbox_100ms_features.csv"
OUT = BACH_ROOT / "analysis" / "beta_sync_100ms" / "bach_100ms_audio_midi_tapping_feature_vectors.csv"

KEY_COLS = ["stim_name", "wtc_code", "bin_index", "bin_start_s", "bin_end_s", "bin_center_s"]


def round_time_keys(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["bin_start_s", "bin_end_s", "bin_center_s"]:
        if col in out:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(6)
    return out


def feature_cols(df: pd.DataFrame, prefixes: tuple[str, ...]) -> list[str]:
    meta = set(KEY_COLS + ["bin_width_s", "source_audio_path"])
    return [col for col in df.columns if col not in meta and col.startswith(prefixes)]


def maybe_join(base: pd.DataFrame, path: Path, prefixes: tuple[str, ...], label: str) -> pd.DataFrame:
    if not path.exists():
        print(f"Skipping {label}; missing {path}")
        return base
    features = round_time_keys(pd.read_csv(path, low_memory=False))
    cols = [col for col in KEY_COLS if col in base.columns and col in features.columns]
    if cols != KEY_COLS:
        raise RuntimeError(f"{label} is missing expected join keys: {set(KEY_COLS) - set(cols)}")
    keep_cols = cols + feature_cols(features, prefixes)
    return base.merge(features[keep_cols], on=cols, how="left", validate="one_to_one")


def main() -> None:
    base = round_time_keys(pd.read_csv(BASE_100MS, low_memory=False))
    joined = maybe_join(base, PY_AUDIO_100MS, ("audio100_",), "Python 100 ms audio")
    joined = maybe_join(joined, MIRTOOLBOX_100MS, ("mir100_",), "MIRToolbox 100 ms")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    joined.to_csv(OUT, index=False)
    print(OUT)
    print(f"rows={len(joined)} tracks={joined['stim_name'].nunique()} columns={len(joined.columns)}")


if __name__ == "__main__":
    main()
