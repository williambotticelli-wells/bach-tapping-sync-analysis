#!/usr/bin/env python3
"""Build 100 ms acoustic feature vectors for Bach analyses.

This is a dependency-light companion to `bach_run_100ms_mirtoolbox_features.m`.
It uses the same first-musical-onset clock and 100 ms bins as the MIDI/tapping
vectors, making the output suitable for emotion/ECoG joins.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
import pandas as pd


BACH_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = BACH_ROOT / "alignment" / "beta_midi_sync_draft" / "bach_beta_midi_sync_manifest.csv"
OUT_DIR = BACH_ROOT / "analysis" / "beta_sync_100ms"
BIN_S = 0.100
ROLLOFF_FRAC = 0.85


def read_wav_mono(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        channels = wf.getnchannels()
        width = wf.getsampwidth()
        frames = wf.readframes(wf.getnframes())
    if width == 2:
        y = np.frombuffer(frames, dtype="<i2").astype(float) / 32768.0
    elif width == 4:
        y = np.frombuffer(frames, dtype="<i4").astype(float) / 2147483648.0
    else:
        y = np.frombuffer(frames, dtype=np.uint8).astype(float)
        y = (y - 128.0) / 128.0
    if channels > 1:
        y = y.reshape(-1, channels).mean(axis=1)
    return y, sr


def spectral_features(segment: np.ndarray, sr: int) -> dict[str, float]:
    if segment.size == 0:
        return {
            "audio100_spectral_centroid_hz": np.nan,
            "audio100_spectral_bandwidth_hz": np.nan,
            "audio100_spectral_rolloff_hz": np.nan,
        }
    window = np.hanning(segment.size)
    spectrum = np.abs(np.fft.rfft(segment * window))
    freqs = np.fft.rfftfreq(segment.size, 1.0 / sr)
    mag_sum = float(spectrum.sum())
    if mag_sum <= 0:
        return {
            "audio100_spectral_centroid_hz": 0.0,
            "audio100_spectral_bandwidth_hz": 0.0,
            "audio100_spectral_rolloff_hz": 0.0,
        }
    centroid = float((freqs * spectrum).sum() / mag_sum)
    bandwidth = float(np.sqrt((((freqs - centroid) ** 2) * spectrum).sum() / mag_sum))
    cume = np.cumsum(spectrum)
    rolloff_idx = int(np.searchsorted(cume, ROLLOFF_FRAC * cume[-1]))
    rolloff_idx = min(rolloff_idx, len(freqs) - 1)
    return {
        "audio100_spectral_centroid_hz": centroid,
        "audio100_spectral_bandwidth_hz": bandwidth,
        "audio100_spectral_rolloff_hz": float(freqs[rolloff_idx]),
    }


def summarize_segment(segment: np.ndarray, sr: int, prev_rms: float | None) -> dict[str, float]:
    if segment.size == 0:
        rms = np.nan
        zcr = np.nan
    else:
        rms = float(np.sqrt(np.mean(segment**2)))
        zcr = float(np.mean(np.abs(np.diff(np.signbit(segment).astype(int))))) if segment.size > 1 else 0.0
    out = {
        "audio100_rms": rms,
        "audio100_zero_crossing_rate": zcr,
        "audio100_onset_strength_proxy": max(0.0, rms - prev_rms) if prev_rms is not None and np.isfinite(rms) else 0.0,
    }
    out.update(spectral_features(segment, sr))
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(MANIFEST, dtype=str).fillna("")
    rows = []
    inventory_rows = []
    for _, meta in manifest.iterrows():
        stim = str(meta["stim_name"])
        wtc = str(meta["wtc_code"])
        wav_path = Path(str(meta["deployed_t0_wav"]))
        if not wav_path.exists():
            inventory_rows.append(
                {
                    "stim_name": stim,
                    "wtc_code": wtc,
                    "source_audio_path": str(wav_path),
                    "duration_s": np.nan,
                    "sample_rate": np.nan,
                    "n_100ms_bins": 0,
                    "status": "missing_wav",
                }
            )
            continue
        y, sr = read_wav_mono(wav_path)
        duration = len(y) / sr if sr > 0 else 0.0
        n_bins = int(np.ceil(duration / BIN_S)) if duration > 0 else 0
        prev_rms: float | None = None
        for idx in range(n_bins):
            start = round(idx * BIN_S, 10)
            end = min(duration, start + BIN_S)
            lo = int(round(start * sr))
            hi = min(len(y), int(round(end * sr)))
            segment = y[lo:hi]
            features = summarize_segment(segment, sr, prev_rms)
            prev_rms = features["audio100_rms"]
            row = {
                "stim_name": stim,
                "wtc_code": wtc,
                "bin_index": idx,
                "bin_start_s": start,
                "bin_end_s": end,
                "bin_center_s": (start + end) / 2.0,
                "bin_width_s": end - start,
                "source_audio_path": str(wav_path),
            }
            row.update(features)
            rows.append(row)
        inventory_rows.append(
            {
                "stim_name": stim,
                "wtc_code": wtc,
                "source_audio_path": str(wav_path),
                "duration_s": duration,
                "sample_rate": sr,
                "n_100ms_bins": n_bins,
                "status": "exported",
            }
        )
    features = pd.DataFrame(rows)
    inventory = pd.DataFrame(inventory_rows)
    features.to_csv(OUT_DIR / "bach_100ms_audio_feature_vectors.csv", index=False)
    inventory.to_csv(OUT_DIR / "bach_100ms_audio_feature_inventory.csv", index=False)
    print(OUT_DIR / "bach_100ms_audio_feature_vectors.csv")
    print(f"rows={len(features)} tracks={features['stim_name'].nunique() if not features.empty else 0}")


if __name__ == "__main__":
    main()
