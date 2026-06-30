#!/usr/bin/env python3
"""Run GlobalTap-style tapping analyses on the beta-sync Bach data.

This extends the exploratory Bach tables with methods closer to the ISMIR
GlobalTap paper: MAD-filtered KDE peaks, an optimized near-isochronous grid on
the first 30 s, split-half reliability/convergence, MIDI-onset agreement screens,
and click-track previews. MIDI onset agreement is not a beat-reference score; it
is included only as a synchronization/event-structure diagnostic.
"""

from __future__ import annotations

import json
import math
import sys
import wave
import argparse
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import find_peaks


SCRIPT_DIR = Path(__file__).resolve().parent
BACH_ROOT = SCRIPT_DIR.parents[0]
GT_ROOT = BACH_ROOT.parents[0]
OPT_ROOT = GT_ROOT / "companion_repo" / "optimization"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(OPT_ROOT) not in sys.path:
    sys.path.insert(0, str(OPT_ROOT))

from build_three_file_sync_packet import parse_midi_note_events  # noqa: E402
from compute_bach_tap_metrics import taps_from_row  # noqa: E402
import run_pipeline as gt_opt  # noqa: E402


MANIFEST = BACH_ROOT / "alignment" / "beta_midi_sync_draft" / "bach_beta_midi_sync_manifest.csv"
TAP_INPUT = (
    BACH_ROOT
    / "bach-tap-data/bach-tap/bach-tapping/bach-tapping-data/database/derived/"
    "tap_all_trials_combined_usable.csv"
)
OUT_DIR = BACH_ROOT / "analysis" / "beta_globaltap_canonical"
CLICK_DIR = OUT_DIR / "click_previews_first30s"

KDE_DT = 0.005
KDE_BW = 0.080
PEAK_PROM_FRAC = 0.10
MIN_PEAK_DISTANCE_S = 0.150
MAD_MULT = 3.5
F_TOL_S = 0.070
SPLIT_ITER = 200
WINDOW_START_S = 0.0
WINDOW_END_S = 30.0


@dataclass
class TrackTaps:
    stim_name: str
    wtc_code: str
    arrays: list[tuple[str, np.ndarray]]
    duration_s: float
    midi_path: Path
    audio_path: Path


def load_tracks() -> list[TrackTaps]:
    manifest = pd.read_csv(MANIFEST, dtype=str).fillna("")
    tap_df = pd.read_csv(TAP_INPUT, low_memory=False)
    if "usable" in tap_df.columns:
        tap_df = tap_df[tap_df["usable"].fillna(False).astype(bool)].copy()
    onset_by_stim = dict(zip(manifest["stim_name"], pd.to_numeric(manifest["manual_onset_s"], errors="coerce").fillna(0.0)))
    tracks = []
    for _, mrow in manifest.iterrows():
        stim = mrow["stim_name"]
        offset = float(onset_by_stim.get(stim, 0.0))
        sub = tap_df[tap_df["stim_name"].astype(str) == stim]
        arrays = []
        for _, row in sub.iterrows():
            taps = taps_from_row(row) - offset
            taps = taps[np.isfinite(taps)]
            taps = taps[taps >= 0]
            if taps.size:
                pid = str(row.get("participant_uid", row.get("participant_id", "")))
                arrays.append((pid, np.sort(taps)))
        duration = float(pd.to_numeric(pd.Series([mrow.get("deployed_t0_duration_s", "")]), errors="coerce").fillna(0.0).iloc[0])
        tracks.append(
            TrackTaps(
                stim_name=stim,
                wtc_code=mrow["wtc_code"],
                arrays=arrays,
                duration_s=duration,
                midi_path=Path(mrow["beta_midi_path"]),
                audio_path=Path(mrow["deployed_t0_wav"]),
            )
        )
    return tracks


def pooled_taps(arrays: list[tuple[str, np.ndarray]], w0: float, w1: float) -> np.ndarray:
    if not arrays:
        return np.array([])
    taps = np.concatenate([arr for _, arr in arrays])
    taps = taps[np.isfinite(taps)]
    return np.sort(taps[(taps >= w0) & (taps <= w1)])


def kde_curve(taps: np.ndarray, w0: float, w1: float) -> tuple[np.ndarray, np.ndarray]:
    grid = np.arange(w0, w1 + KDE_DT, KDE_DT)
    density = np.zeros_like(grid)
    if taps.size == 0:
        return grid, density
    for tap in taps:
        density += np.exp(-0.5 * ((grid - tap) / KDE_BW) ** 2)
    density /= max(1, taps.size) * KDE_BW * math.sqrt(2 * math.pi)
    return grid, density


def extract_peaks(grid: np.ndarray, density: np.ndarray) -> np.ndarray:
    if density.size == 0 or float(np.nanmax(density)) <= 0:
        return np.array([])
    distance = max(1, int(round(MIN_PEAK_DISTANCE_S / KDE_DT)))
    peaks, _props = find_peaks(
        density,
        distance=distance,
        prominence=PEAK_PROM_FRAC * float(np.nanmax(density)),
    )
    return grid[peaks]


def mad_filtered_peaks(taps: np.ndarray, w0: float, w1: float) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    grid, density = kde_curve(taps, w0, w1)
    prelim = extract_peaks(grid, density)
    if taps.size == 0 or prelim.size == 0:
        return prelim, taps, {"n_raw_taps": int(taps.size), "n_filtered_taps": int(taps.size), "mad_s": np.nan}
    nearest_dist = np.min(np.abs(taps[:, None] - prelim[None, :]), axis=1)
    med = float(np.median(nearest_dist))
    mad = float(np.median(np.abs(nearest_dist - med)))
    # Robust fallback: if MAD is zero, keep taps within a broad 150 ms envelope.
    threshold = MAD_MULT * mad if mad > 0 else MIN_PEAK_DISTANCE_S
    keep = nearest_dist <= threshold
    filtered = taps[keep]
    f_grid, f_density = kde_curve(filtered, w0, w1)
    final_peaks = extract_peaks(f_grid, f_density)
    return final_peaks, filtered, {
        "n_raw_taps": int(taps.size),
        "n_filtered_taps": int(filtered.size),
        "mad_s": mad,
        "mad_threshold_s": threshold,
        "tap_retention": float(filtered.size / taps.size) if taps.size else np.nan,
        "n_prelim_peaks": int(prelim.size),
        "n_filtered_peaks": int(final_peaks.size),
    }


def ioi_cv(beats: np.ndarray) -> float:
    if beats.size < 3:
        return np.nan
    iois = np.diff(np.sort(beats))
    return float(np.std(iois, ddof=1) / np.mean(iois)) if np.mean(iois) > 0 else np.nan


def f_measure(est: np.ndarray, ref: np.ndarray, tol_s: float = F_TOL_S) -> dict[str, float]:
    est = np.sort(est[np.isfinite(est)])
    ref = np.sort(ref[np.isfinite(ref)])
    if est.size == 0 or ref.size == 0:
        return {"precision": np.nan, "recall": np.nan, "f_measure": np.nan, "matches": 0, "n_est": int(est.size), "n_ref": int(ref.size)}
    used = np.zeros(ref.size, dtype=bool)
    matches = 0
    for e in est:
        idx = np.where(~used)[0]
        if idx.size == 0:
            break
        nearest_local = idx[np.argmin(np.abs(ref[idx] - e))]
        if abs(ref[nearest_local] - e) <= tol_s:
            used[nearest_local] = True
            matches += 1
    precision = matches / est.size
    recall = matches / ref.size
    f = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
    return {"precision": precision, "recall": recall, "f_measure": f, "matches": matches, "n_est": int(est.size), "n_ref": int(ref.size)}


def midi_note_onsets(midi_path: Path, w0: float, w1: float) -> np.ndarray:
    if not midi_path.exists():
        return np.array([])
    notes = parse_midi_note_events(midi_path)
    if not notes:
        return np.array([])
    first = min(n[0] for n in notes)
    starts = np.array([n[0] - first for n in notes], dtype=float)
    starts = starts[np.isfinite(starts)]
    return np.sort(starts[(starts >= w0) & (starts <= w1)])


def optimize_grid(stim: str, peaks: np.ndarray, w0: float, w1: float, istc: float) -> dict:
    """Run the canonical companion-repo GlobalTap optimizer cascade."""
    peaks = np.sort(peaks[(peaks >= w0) & (peaks <= w1)])
    if peaks.size < 3:
        return {"stem": stim, "crowd_beats": np.array([]), "path": ["FAIL:not_enough_peaks"]}
    old_w0, old_w1 = gt_opt.W0, gt_opt.W1
    try:
        gt_opt.W0 = w0
        gt_opt.W1 = w1
        return gt_opt.run_cascade(stim, peaks, np.array([]), istc)
    finally:
        gt_opt.W0, gt_opt.W1 = old_w0, old_w1


def split_half_reliability(track: TrackTaps, rng: np.random.Generator, split_iter: int) -> dict[str, float]:
    arrays = [(pid, arr[(arr >= WINDOW_START_S) & (arr <= WINDOW_END_S)]) for pid, arr in track.arrays]
    arrays = [(pid, arr) for pid, arr in arrays if arr.size]
    if len(arrays) < 4:
        return {
            "stim_name": track.stim_name,
            "n_participants": len(arrays),
            "split_iterations": 0,
            "kde_curve_r_mean": np.nan,
            "peak_f_mean": np.nan,
        }
    rs, fs = [], []
    for _ in range(split_iter):
        perm = rng.permutation(len(arrays))
        half = len(perm) // 2
        a = [arrays[i] for i in perm[:half]]
        b = [arrays[i] for i in perm[half:]]
        taps_a = pooled_taps(a, WINDOW_START_S, WINDOW_END_S)
        taps_b = pooled_taps(b, WINDOW_START_S, WINDOW_END_S)
        grid_a, den_a = kde_curve(taps_a, WINDOW_START_S, WINDOW_END_S)
        _grid_b, den_b = kde_curve(taps_b, WINDOW_START_S, WINDOW_END_S)
        if np.std(den_a) > 0 and np.std(den_b) > 0:
            rs.append(float(np.corrcoef(den_a, den_b)[0, 1]))
        peaks_a = extract_peaks(grid_a, den_a)
        peaks_b = extract_peaks(grid_a, den_b)
        fs.append(f_measure(peaks_a, peaks_b)["f_measure"])
    return {
        "stim_name": track.stim_name,
        "n_participants": len(arrays),
        "split_iterations": split_iter,
        "kde_curve_r_mean": float(np.nanmean(rs)) if rs else np.nan,
        "kde_curve_r_sd": float(np.nanstd(rs, ddof=1)) if len(rs) > 1 else np.nan,
        "peak_f_mean": float(np.nanmean(fs)) if fs else np.nan,
        "peak_f_sd": float(np.nanstd(fs, ddof=1)) if len(fs) > 1 else np.nan,
    }


def convergence_curve(track: TrackTaps, rng: np.random.Generator, reps_per_sample: int) -> list[dict[str, float]]:
    arrays = [(pid, arr[(arr >= WINDOW_START_S) & (arr <= WINDOW_END_S)]) for pid, arr in track.arrays]
    arrays = [(pid, arr) for pid, arr in arrays if arr.size]
    n = len(arrays)
    if n < 4:
        return []
    all_taps = pooled_taps(arrays, WINDOW_START_S, WINDOW_END_S)
    grid_ref, den_ref = kde_curve(all_taps, WINDOW_START_S, WINDOW_END_S)
    peak_ref = extract_peaks(grid_ref, den_ref)
    sample_sizes = sorted(set([2, 3, 4, 5, max(2, n // 2), n]))
    rows = []
    for k in sample_sizes:
        if k > n:
            continue
        rs, fs = [], []
        reps = reps_per_sample if k < n else 1
        for _ in range(reps):
            chosen = arrays if k == n else [arrays[i] for i in rng.choice(n, size=k, replace=False)]
            taps = pooled_taps(chosen, WINDOW_START_S, WINDOW_END_S)
            grid, den = kde_curve(taps, WINDOW_START_S, WINDOW_END_S)
            if np.std(den) > 0 and np.std(den_ref) > 0:
                rs.append(float(np.corrcoef(den, den_ref)[0, 1]))
            peaks = extract_peaks(grid, den)
            fs.append(f_measure(peaks, peak_ref)["f_measure"])
        rows.append({
            "stim_name": track.stim_name,
            "n_participants_total": n,
            "sample_size": k,
            "kde_curve_r_to_full_mean": float(np.nanmean(rs)) if rs else np.nan,
            "peak_f_to_full_mean": float(np.nanmean(fs)) if fs else np.nan,
        })
    return rows


def read_wav_mono(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        frames = wf.readframes(wf.getnframes())
    if sampwidth == 2:
        arr = np.frombuffer(frames, dtype="<i2").astype(float) / 32768.0
    elif sampwidth == 4:
        arr = np.frombuffer(frames, dtype="<i4").astype(float) / 2147483648.0
    else:
        arr = np.frombuffer(frames, dtype=np.uint8).astype(float)
        arr = (arr - 128.0) / 128.0
    if n_channels > 1:
        arr = arr.reshape(-1, n_channels).mean(axis=1)
    return arr, sr


def write_wav_mono(path: Path, audio: np.ndarray, sr: int) -> None:
    audio = np.asarray(audio, dtype=float)
    peak = np.max(np.abs(audio)) if audio.size else 1.0
    if peak > 1:
        audio = audio / peak
    pcm = np.clip(audio, -1, 1)
    pcm = (pcm * 32767).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def render_click_preview(track: TrackTaps, beats: np.ndarray, click_dir: Path) -> str:
    if not track.audio_path.exists() or beats.size == 0:
        return ""
    y, sr = read_wav_mono(track.audio_path)
    n = min(len(y), int(WINDOW_END_S * sr))
    y = y[:n]
    click = np.zeros_like(y)
    click_len = max(1, int(0.012 * sr))
    env = np.hanning(click_len * 2)[:click_len]
    tone = np.sin(2 * np.pi * 1100 * np.arange(click_len) / sr) * env
    for beat in beats:
        idx = int(round(beat * sr))
        if 0 <= idx < len(click):
            end = min(len(click), idx + click_len)
            click[idx:end] += tone[: end - idx]
    music = y / max(1e-9, np.max(np.abs(y))) * 0.35
    clicks = click / max(1e-9, np.max(np.abs(click))) * 0.65 if np.max(np.abs(click)) > 0 else click
    out = music + clicks
    out_path = click_dir / f"{track.stim_name}_crowd_grid_clicks_first30s.wav"
    write_wav_mono(out_path, out, sr)
    return str(out_path)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def analyze_track(
    track: TrackTaps,
    seed: int,
    split_iter: int,
    convergence_reps: int,
    skip_clicks: bool,
    click_dir: Path,
) -> dict:
    rng = np.random.default_rng(seed)
    w0 = WINDOW_START_S
    w1 = min(WINDOW_END_S, track.duration_s if track.duration_s > 0 else WINDOW_END_S)
    taps = pooled_taps(track.arrays, w0, w1)
    peaks, filtered_taps, filt = mad_filtered_peaks(taps, w0, w1)
    del filtered_taps
    split_row = split_half_reliability(track, rng, split_iter)
    conv_rows = convergence_curve(track, rng, convergence_reps)
    diag = optimize_grid(track.stim_name, peaks, w0, w1, np.nan)
    beats = np.asarray(diag.get("crowd_beats", []), dtype=float)
    diag_serializable = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in diag.items()}
    midi_onsets = midi_note_onsets(track.midi_path, w0, w1)
    midi_f = f_measure(beats, midi_onsets)
    click_path = "" if skip_clicks else render_click_preview(track, beats, click_dir)

    peak_rows = [
        {
            "stim_name": track.stim_name,
            "wtc_code": track.wtc_code,
            "peak_index": i,
            "filtered_kde_peak_s": float(peak),
        }
        for i, peak in enumerate(peaks, start=1)
    ]
    beat_rows = [
        {
            "stim_name": track.stim_name,
            "wtc_code": track.wtc_code,
            "beat_index": i,
            "optimized_crowd_beat_s": float(beat),
        }
        for i, beat in enumerate(beats, start=1)
    ]
    f_row = {
        "stim_name": track.stim_name,
        "wtc_code": track.wtc_code,
        "comparison": "optimized_crowd_beats_vs_midi_note_onsets_not_beat_reference",
        **midi_f,
    }
    track_row = {
        "stim_name": track.stim_name,
        "wtc_code": track.wtc_code,
        "analysis_window_start_s": w0,
        "analysis_window_end_s": w1,
        "n_participants": len(track.arrays),
        "n_raw_taps_window": filt["n_raw_taps"],
        "n_filtered_taps_window": filt["n_filtered_taps"],
        "tap_retention_after_mad": filt.get("tap_retention", np.nan),
        "n_filtered_kde_peaks": int(peaks.size),
        "n_optimized_beats": int(beats.size),
        "optimized_beat_cv_ioi": ioi_cv(beats),
        "optimized_median_ioi_s": float(np.median(np.diff(beats))) if beats.size > 2 else np.nan,
        "optimized_tempo_bpm": float(60.0 / np.median(np.diff(beats))) if beats.size > 2 and np.median(np.diff(beats)) > 0 else np.nan,
        "optimizer_label": diag.get("crowd_label", ""),
        "optimizer_path": "|".join(diag.get("path", [])),
        "bimodal_score": diag.get("bimodal_score", np.nan),
        "grid_extension_activated": diag.get("ge_activated", False),
        "midi_onset_f_measure_diagnostic": midi_f["f_measure"],
        "click_preview_path": click_path,
    }
    return {
        "stim_name": track.stim_name,
        "peak_rows": peak_rows,
        "beat_rows": beat_rows,
        "track_row": track_row,
        "f_row": f_row,
        "split_row": split_row,
        "conv_rows": conv_rows,
        "diag_row": diag_serializable,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    parser.add_argument("--stim-name", default="", help="Run a single stimulus for smoke testing.")
    parser.add_argument("--split-iter", type=int, default=SPLIT_ITER)
    parser.add_argument("--convergence-reps", type=int, default=200)
    parser.add_argument("--skip-clicks", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    click_dir = out_dir / "click_previews_first30s"
    out_dir.mkdir(parents=True, exist_ok=True)
    click_dir.mkdir(parents=True, exist_ok=True)
    tracks = load_tracks()
    if args.stim_name:
        tracks = [track for track in tracks if track.stim_name == args.stim_name]
        if not tracks:
            raise SystemExit(f"No matching stim_name: {args.stim_name}")

    peak_rows = []
    beat_rows = []
    track_rows = []
    f_rows = []
    split_rows = []
    conv_rows = []
    diag_rows = []

    jobs = [(track, 20260630 + i) for i, track in enumerate(tracks)]
    if args.workers == 1:
        results = []
        for track, seed in jobs:
            print(f"Analyzing {track.stim_name}", flush=True)
            results.append(
                analyze_track(track, seed, args.split_iter, args.convergence_reps, args.skip_clicks, click_dir)
            )
    else:
        results = []
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(
                    analyze_track,
                    track,
                    seed,
                    args.split_iter,
                    args.convergence_reps,
                    args.skip_clicks,
                    click_dir,
                ): track.stim_name
                for track, seed in jobs
            }
            for future in as_completed(futures):
                stim = futures[future]
                print(f"Finished {stim}", flush=True)
                results.append(future.result())

    for result in sorted(results, key=lambda row: row["stim_name"]):
        peak_rows.extend(result["peak_rows"])
        beat_rows.extend(result["beat_rows"])
        track_rows.append(result["track_row"])
        f_rows.append(result["f_row"])
        split_rows.append(result["split_row"])
        conv_rows.extend(result["conv_rows"])
        diag_rows.append(result["diag_row"])

    pd.DataFrame(track_rows).to_csv(out_dir / "bach_globaltap_style_track_summary.csv", index=False)
    pd.DataFrame(peak_rows).to_csv(out_dir / "mad_filtered_kde_peaks_first30s.csv", index=False)
    pd.DataFrame(beat_rows).to_csv(out_dir / "optimized_crowd_beats_first30s.csv", index=False)
    pd.DataFrame(f_rows).to_csv(out_dir / "midi_onset_agreement_diagnostics.csv", index=False)
    pd.DataFrame(split_rows).to_csv(out_dir / "split_half_reliability_first30s.csv", index=False)
    pd.DataFrame(conv_rows).to_csv(out_dir / "convergence_to_full_density_first30s.csv", index=False)
    write_jsonl(out_dir / "optimizer_diagnostics.jsonl", diag_rows)

    summary = pd.DataFrame(track_rows)
    split = pd.DataFrame(split_rows)
    lines = [
        "# Bach GlobalTap-Style Analysis Summary",
        "",
        f"- Tracks analyzed: {len(summary)}",
        f"- Median optimized beat CV IOI: {summary['optimized_beat_cv_ioi'].median():.4f}",
        f"- Median optimized tempo BPM: {summary['optimized_tempo_bpm'].median():.2f}",
        f"- Median split-half KDE r: {split['kde_curve_r_mean'].median():.3f}",
        f"- Median split-half peak F: {split['peak_f_mean'].median():.3f}",
        "",
        "Caveat: MIDI-onset agreement is an event/sync diagnostic, not a true beat-reference F-measure.",
    ]
    (out_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote Bach GlobalTap-style analyses to {out_dir}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
