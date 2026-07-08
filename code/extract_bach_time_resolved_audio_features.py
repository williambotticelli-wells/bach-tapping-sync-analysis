#!/usr/bin/env python3
"""Extract time-resolved Bach audio features for tap/neural correlations.

This is the Python counterpart to the MIRToolbox plan: it exports frame-wise
features rather than only whole-piece means. Frame times are reported both in
file time and in the aligned analysis clock when a first-onset offset is present
in the Bach alignment manifest.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


BACH_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = BACH_ROOT / "alignment/bach_alignment_manifest_verified.csv"
DEFAULT_OUT = BACH_ROOT / "alignment/audio_features"


def load_wav_mono(path: Path, target_sr: int | None = None) -> tuple[np.ndarray, int]:
    import wave

    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        channels = wf.getnchannels()
        width = wf.getsampwidth()
        frames = wf.readframes(wf.getnframes())
    if width == 2:
        data = np.frombuffer(frames, dtype="<i2").astype(float) / 32768.0
    elif width == 4:
        data = np.frombuffer(frames, dtype="<i4").astype(float) / 2147483648.0
    else:
        raise RuntimeError(f"Unsupported WAV sample width {width}: {path}")
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    # Keep the fallback dependency-free; do not resample without scipy/librosa.
    return data, sr


def maybe_librosa():
    try:
        import librosa  # type: ignore
    except ImportError as exc:
        return None
    return librosa


def parse_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return default
        text = str(value).strip()
        if not text:
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def choose_audio_path(row: pd.Series, prefer: str) -> Path | None:
    # "alt_source" is a second-source WAV column on the private alignment
    # manifest (kept as a fallback alias below for manifests built before
    # that column was renamed for this collaborator package).
    alt_source_cols = ["alt_source_wav_path", "rena_wav_path"]
    columns = (
        alt_source_cols + ["collective_wav_path"]
        if prefer == "alt_source"
        else ["collective_wav_path"] + alt_source_cols
    )
    for col in columns:
        path = Path(str(row.get(col, "")).strip()).expanduser()
        if str(path) and path.exists() and path.suffix.lower() == ".wav":
            return path
    return None


def extract_features_librosa(path: Path, sr: int, hop_length: int, frame_length: int) -> pd.DataFrame:
    librosa = maybe_librosa()
    if librosa is None:
        return pd.DataFrame()
    y, sr_actual = librosa.load(path, sr=sr, mono=True)
    if y.size == 0:
        return pd.DataFrame()

    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr_actual, hop_length=hop_length)[0]
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr_actual, hop_length=hop_length)[0]
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr_actual, hop_length=hop_length)[0]
    zcr = librosa.feature.zero_crossing_rate(y, frame_length=frame_length, hop_length=hop_length)[0]
    onset_env = librosa.onset.onset_strength(y=y, sr=sr_actual, hop_length=hop_length)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr_actual, hop_length=hop_length)
    chroma_strength = chroma.mean(axis=0)

    n = min(len(rms), len(centroid), len(bandwidth), len(rolloff), len(zcr), len(onset_env), len(chroma_strength))
    times = librosa.frames_to_time(np.arange(n), sr=sr_actual, hop_length=hop_length)
    return pd.DataFrame({
        "time_s_file": times,
        "rms": rms[:n],
        "spectral_centroid_hz": centroid[:n],
        "spectral_bandwidth_hz": bandwidth[:n],
        "spectral_rolloff_hz": rolloff[:n],
        "zero_crossing_rate": zcr[:n],
        "onset_strength": onset_env[:n],
        "chroma_strength_mean": chroma_strength[:n],
    })


def extract_features_numpy(path: Path, hop_ms: float, frame_ms: float) -> pd.DataFrame:
    y, sr = load_wav_mono(path)
    if y.size == 0:
        return pd.DataFrame()
    hop = max(1, int(round(sr * hop_ms / 1000.0)))
    frame = max(hop, int(round(sr * frame_ms / 1000.0)))
    starts = np.arange(0, max(1, len(y) - frame + 1), hop)
    window = np.hanning(frame)
    freqs = np.fft.rfftfreq(frame, 1.0 / sr)
    rows = []
    prev_rms = None
    for start in starts:
        segment = y[start:start + frame]
        if len(segment) < frame:
            segment = np.pad(segment, (0, frame - len(segment)))
        rms = float(np.sqrt(np.mean(segment ** 2)))
        zcr = float(np.mean(np.abs(np.diff(np.signbit(segment).astype(int)))))
        spectrum = np.abs(np.fft.rfft(segment * window))
        mag_sum = float(spectrum.sum())
        if mag_sum > 0:
            centroid = float((freqs * spectrum).sum() / mag_sum)
            bandwidth = float(np.sqrt((((freqs - centroid) ** 2) * spectrum).sum() / mag_sum))
            cume = np.cumsum(spectrum)
            rolloff = float(freqs[np.searchsorted(cume, 0.85 * cume[-1])])
        else:
            centroid = bandwidth = rolloff = 0.0
        onset_strength = max(0.0, rms - prev_rms) if prev_rms is not None else 0.0
        prev_rms = rms
        rows.append({
            "time_s_file": float(start / sr),
            "rms": rms,
            "spectral_centroid_hz": centroid,
            "spectral_bandwidth_hz": bandwidth,
            "spectral_rolloff_hz": rolloff,
            "zero_crossing_rate": zcr,
            "onset_strength": onset_strength,
            "chroma_strength_mean": np.nan,
        })
    return pd.DataFrame(rows)


def extract_features(path: Path, sr: int, hop_length: int, frame_length: int, hop_ms: float, frame_ms: float) -> pd.DataFrame:
    features = extract_features_librosa(path, sr, hop_length, frame_length)
    if not features.empty:
        return features
    return extract_features_numpy(path, hop_ms, frame_ms)


def write_summary(features: pd.DataFrame, out_dir: Path) -> None:
    if features.empty:
        (out_dir / "SUMMARY.md").write_text("# Bach Audio Features\n\nNo features extracted.\n")
        return
    summary = (
        features.groupby("stimulus_id")
        .agg(
            n_frames=("time_s_file", "count"),
            duration_file_s=("time_s_file", "max"),
            rms_mean=("rms", "mean"),
            onset_strength_mean=("onset_strength", "mean"),
            spectral_centroid_mean_hz=("spectral_centroid_hz", "mean"),
        )
        .reset_index()
    )
    summary.to_csv(out_dir / "audio_feature_summary.csv", index=False)
    lines = [
        "# Bach Time-Resolved Audio Features",
        "",
        f"- Stimuli with extracted features: {summary['stimulus_id'].nunique()}",
        f"- Frames exported: {len(features)}",
        "",
        "The long table `audio_features_time_resolved.csv` is suitable for joining",
        "with `istc_time_resolved.csv`, sliding tap coherence, emotion-slider",
        "traces, or neural/ECoG features by aligned time.",
    ]
    (out_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--prefer", choices=["collective", "alt_source"], default="collective")
    ap.add_argument("--sr", type=int, default=22050)
    ap.add_argument("--hop-ms", type=float, default=25.0)
    ap.add_argument("--frame-ms", type=float, default=100.0)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(args.manifest, dtype=str).fillna("")
    hop_length = max(1, int(round(args.sr * args.hop_ms / 1000.0)))
    frame_length = max(hop_length, int(round(args.sr * args.frame_ms / 1000.0)))

    rows = []
    for _, row in manifest.iterrows():
        path = choose_audio_path(row, args.prefer)
        if path is None:
            continue
        onset = parse_float(row.get("collective_wav_first_onset_s"), 0.0)
        feats = extract_features(path, args.sr, hop_length, frame_length, args.hop_ms, args.frame_ms)
        if feats.empty:
            continue
        feats.insert(0, "stimulus_id", row.get("stimulus_id", ""))
        feats.insert(1, "stim_name", row.get("stim_name", ""))
        feats.insert(2, "audio_path", str(path))
        feats["time_s_aligned"] = feats["time_s_file"] - onset
        rows.append(feats)

    features = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    features.to_csv(out_dir / "audio_features_time_resolved.csv", index=False)
    write_summary(features, out_dir)
    print(f"Wrote audio features to {out_dir}")


if __name__ == "__main__":
    main()
