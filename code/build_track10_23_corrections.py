#!/usr/bin/env python3
"""Onset estimation and stacked-plot helpers for Bach sync QA scripts."""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np


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
        raise ValueError(f"Unsupported WAV width {width}: {path}")
    if channels > 1:
        y = y.reshape(-1, channels).mean(axis=1)
    return y, sr


def estimate_onset_s(path: Path, max_scan_s: float = 5.0) -> float:
    y, sr = read_wav_mono(path)
    y = y[: int(max_scan_s * sr)]
    if len(y) == 0:
        return 0.0
    frame = max(1, int(0.005 * sr))
    hop = max(1, int(0.001 * sr))
    rms = []
    times = []
    for start in range(0, max(1, len(y) - frame), hop):
        chunk = y[start:start + frame]
        rms.append(float(np.sqrt(np.mean(chunk * chunk))))
        times.append(start / sr)
    rms_arr = np.asarray(rms)
    if len(rms_arr) == 0:
        return 0.0
    noise = float(np.percentile(rms_arr[: max(10, len(rms_arr) // 10)], 50))
    peak = float(np.percentile(rms_arr, 99))
    threshold = max(noise * 8.0, peak * 0.08, 1e-4)
    hits = np.where(rms_arr >= threshold)[0]
    return float(times[int(hits[0])]) if len(hits) else 0.0


def plot_stacked(track: str, files: list[tuple[str, Path]], review_onset_s: float, out_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(len(files), 1, figsize=(12, 7), sharex=True)
    if len(files) == 1:
        axes = [axes]
    lo_s = max(0.0, review_onset_s - 0.75)
    hi_s = review_onset_s + 4.0
    for ax, (label, path) in zip(axes, files):
        y, sr = read_wav_mono(path)
        lo = int(lo_s * sr)
        hi = min(len(y), int(hi_s * sr))
        t = np.arange(lo, hi) / sr
        segment = y[lo:hi]
        if len(segment) and np.max(np.abs(segment)) > 0:
            segment = segment / np.max(np.abs(segment))
        auto_onset = estimate_onset_s(path)
        ax.plot(t, segment, linewidth=0.6, color="black")
        ax.axvline(review_onset_s, color="tab:blue", linestyle="--", label=f"review onset {review_onset_s:.6f}s")
        ax.axvline(auto_onset, color="tab:red", linestyle=":", label=f"auto onset {auto_onset:.6f}s")
        ax.set_ylabel(label)
        ax.legend(loc="upper right", fontsize=8)
    axes[-1].set_xlabel("file time (s)")
    fig.suptitle(f"{track}: deployed / matched / MIDI piano onset comparison")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)
