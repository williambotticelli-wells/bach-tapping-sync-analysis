#!/usr/bin/env python3
"""Compute Bach tapping metrics from PsyNet/REPP exports.

Outputs trial-level IOI metrics, per-track KDE consensus peaks, canonical
GlobalTap-style ISTC, beat-sequence CV, participant-to-consensus IOI ratios, and
time-resolved coherence windows. Times are stored in seconds on the REPP-aligned
response clock; once the stimulus alignment manifest is verified, downstream
analyses can join to first-onset-corrected stimulus time.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy.stats import gaussian_kde


BACH_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    BACH_ROOT
    / "bach-tap-data/bach-tap/bach-tapping/bach-tapping-data/database/derived/"
    "tap_all_trials_combined.csv"
)
DEFAULT_OUT = BACH_ROOT / "alignment/metrics"
DEFAULT_MANIFEST = BACH_ROOT / "alignment/bach_alignment_manifest_verified.csv"


def parse_list(value: object) -> list[float]:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    if isinstance(value, list):
        raw = value
    else:
        text = str(value).strip()
        if not text:
            return []
        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            try:
                raw = ast.literal_eval(text)
            except (ValueError, SyntaxError):
                return []
    out = []
    for item in raw:
        try:
            val = float(item)
        except (TypeError, ValueError):
            continue
        if np.isfinite(val):
            out.append(val)
    return out


def taps_from_row(row: pd.Series) -> np.ndarray:
    for col in ["taps_s", "tapping_onsets_s"]:
        if col in row and not pd.isna(row[col]):
            vals = parse_list(row[col])
            if vals:
                arr = np.asarray(vals, dtype=float)
                return np.sort(arr[np.isfinite(arr)])
    for col in ["taps_ms", "resp_onsets_aligned", "tapping_onsets_aligned"]:
        if col in row and not pd.isna(row[col]):
            vals = parse_list(row[col])
            if vals:
                arr = np.asarray(vals, dtype=float) / 1000.0
                return np.sort(arr[np.isfinite(arr)])
    if "analysis" in row and not pd.isna(row["analysis"]):
        try:
            payload = json.loads(str(row["analysis"]))
        except json.JSONDecodeError:
            payload = {}
        for key in ["tapping_onsets_aligned", "resp_onsets_aligned"]:
            vals = parse_list(payload.get(key))
            if vals:
                arr = np.asarray(vals, dtype=float) / 1000.0
                return np.sort(arr[np.isfinite(arr)])
        nested_analysis = payload.get("analysis")
        if nested_analysis:
            try:
                nested_payload = json.loads(str(nested_analysis))
            except json.JSONDecodeError:
                nested_payload = {}
            for key in ["tapping_onsets_aligned", "resp_onsets_aligned"]:
                vals = parse_list(nested_payload.get(key))
                if vals:
                    arr = np.asarray(vals, dtype=float) / 1000.0
                    return np.sort(arr[np.isfinite(arr)])
        extracted = payload.get("extracted_onsets")
        if extracted:
            try:
                extracted_payload = json.loads(str(extracted))
            except json.JSONDecodeError:
                extracted_payload = {}
            vals = parse_list(extracted_payload.get("resp_onsets_aligned"))
            if vals:
                arr = np.asarray(vals, dtype=float) / 1000.0
                return np.sort(arr[np.isfinite(arr)])
    return np.array([])


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


def load_alignment_offsets(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    manifest = pd.read_csv(path, dtype=str).fillna("")
    offsets: dict[str, float] = {}
    for _, row in manifest.iterrows():
        offset = parse_float(row.get("collective_wav_first_onset_s"), 0.0)
        for key in [row.get("stim_name", ""), row.get("collective_audio_filename", "")]:
            key_text = str(key).strip()
            if key_text:
                offsets[key_text] = offset
    return offsets


def row_offset_s(row: pd.Series, offsets: dict[str, float]) -> float:
    return offsets.get(
        str(row.get("stim_name", "")).strip(),
        offsets.get(str(row.get("audio_filename", "")).strip(), 0.0),
    )


def trial_metrics(
    df: pd.DataFrame,
    t0: float | None,
    t1: float | None,
    alignment_offsets: dict[str, float],
) -> tuple[pd.DataFrame, dict[str, list[np.ndarray]]]:
    rows = []
    tap_arrays: dict[str, list[np.ndarray]] = {}
    for idx, row in df.iterrows():
        alignment_offset_s = row_offset_s(row, alignment_offsets)
        taps = taps_from_row(row) - alignment_offset_s
        if t0 is not None:
            taps = taps[taps >= t0]
        if t1 is not None:
            taps = taps[taps <= t1]
        iois = np.diff(taps)
        stim = str(row.get("stim_name", row.get("audio_filename", "unknown")))
        participant = str(row.get("participant_uid", row.get("participant_id", "")))
        if taps.size >= 2:
            tap_arrays.setdefault(stim, []).append(taps)
        mean_ioi = float(np.mean(iois)) if iois.size else np.nan
        sd_ioi = float(np.std(iois, ddof=1)) if iois.size > 1 else np.nan
        cv = float(sd_ioi / mean_ioi * 100.0) if np.isfinite(sd_ioi) and mean_ioi > 0 else np.nan
        tempo = float(60.0 / mean_ioi) if mean_ioi > 0 else np.nan
        rows.append({
            "trial_row": idx,
            "stim_name": stim,
            "audio_filename": row.get("audio_filename", ""),
            "alignment_offset_s": alignment_offset_s,
            "participant_uid": participant,
            "usable": row.get("usable", not bool(row.get("failed", False))),
            "n_taps": int(taps.size),
            "mean_ioi_s": mean_ioi,
            "perceived_tempo_bpm": tempo,
            "sd_ioi_s": sd_ioi,
            "cv_ioi_pct": cv,
            "trial_cv_ioi_pct": cv,
            "median_ioi_s": float(np.median(iois)) if iois.size else np.nan,
            "first_tap_s": float(taps[0]) if taps.size else np.nan,
            "last_tap_s": float(taps[-1]) if taps.size else np.nan,
        })
    return pd.DataFrame(rows), tap_arrays


def kde_density(tap_arrays: list[np.ndarray], t_grid: np.ndarray, bandwidth_s: float) -> np.ndarray:
    if not tap_arrays:
        return np.zeros_like(t_grid)
    pooled = np.concatenate(tap_arrays)
    pooled = pooled[np.isfinite(pooled)]
    if pooled.size < 5 or np.std(pooled, ddof=1) <= 0:
        return np.zeros_like(t_grid)
    kde = gaussian_kde(pooled, bw_method=bandwidth_s / np.std(pooled, ddof=1))
    return kde.evaluate(t_grid)


def consensus_tables(
    tap_arrays: dict[str, list[np.ndarray]],
    bandwidth_s: float,
    dt_s: float,
    min_peak_distance_s: float,
    prominence_frac: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    peak_rows = []
    summary_rows = []
    for stim, arrays in sorted(tap_arrays.items()):
        all_taps = np.concatenate(arrays)
        t0 = max(0.0, float(np.nanmin(all_taps)) - 1.0)
        t1 = float(np.nanmax(all_taps)) + 1.0
        t_grid = np.arange(t0, t1 + dt_s, dt_s)
        density = kde_density(arrays, t_grid, bandwidth_s)
        if density.max() > 0:
            distance = max(1, int(round(min_peak_distance_s / dt_s)))
            peaks, props = find_peaks(
                density,
                distance=distance,
                prominence=prominence_frac * density.max(),
            )
            peak_times = t_grid[peaks]
            prominences = props.get("prominences", np.full(len(peaks), np.nan))
        else:
            peak_times = np.array([])
            prominences = np.array([])
        for order, (time_s, prominence) in enumerate(zip(peak_times, prominences), start=1):
            peak_rows.append({
                "stim_name": stim,
                "peak_index": order,
                "consensus_time_s": float(time_s),
                "kde_prominence": float(prominence),
                "n_trials": len(arrays),
                "n_taps": int(all_taps.size),
            })
        consensus_ioi = np.diff(peak_times)
        beat_sequence_cv = (
            float(np.std(consensus_ioi, ddof=1) / np.mean(consensus_ioi))
            if consensus_ioi.size > 1 and np.mean(consensus_ioi) > 0
            else np.nan
        )
        summary_rows.append({
            "stim_name": stim,
            "n_trials": len(arrays),
            "n_taps": int(all_taps.size),
            "n_consensus_peaks": int(len(peak_times)),
            "consensus_mean_ioi_s": float(np.mean(consensus_ioi)) if consensus_ioi.size else np.nan,
            "consensus_median_ioi_s": float(np.median(consensus_ioi)) if consensus_ioi.size else np.nan,
            "beat_sequence_cv_ioi": beat_sequence_cv,
            "beat_sequence_cv_ioi_pct": beat_sequence_cv * 100.0 if np.isfinite(beat_sequence_cv) else np.nan,
            "consensus_tempo_bpm": float(60.0 / np.median(consensus_ioi)) if consensus_ioi.size and np.median(consensus_ioi) > 0 else np.nan,
            "kde_bandwidth_s": bandwidth_s,
        })
    return pd.DataFrame(peak_rows), pd.DataFrame(summary_rows)


def _tap_participant_arrays(sub: pd.DataFrame, alignment_offsets: dict[str, float]) -> list[tuple[str, np.ndarray]]:
    out: list[tuple[str, np.ndarray]] = []
    for _, row in sub.iterrows():
        arr = (taps_from_row(row) - row_offset_s(row, alignment_offsets)) * 1000.0
        if arr.size == 0:
            continue
        pid = str(row.get("participant_uid", row.get("participant_id", "")))
        out.append((pid, arr))
    return out


def _participant_bin_counts(
    participant_taps: list[tuple[str, np.ndarray]],
    centers_ms: np.ndarray,
    bin_ms: float,
) -> tuple[np.ndarray, np.ndarray]:
    tap_counts = np.zeros(centers_ms.size, dtype=int)
    unique_counts = np.zeros(centers_ms.size, dtype=int)
    half = bin_ms / 2.0
    for i, center in enumerate(centers_ms):
        total = 0
        pids = set()
        for pid, arr in participant_taps:
            n = int(((arr >= center - half) & (arr <= center + half)).sum())
            if n:
                total += n
                pids.add(pid)
        tap_counts[i] = total
        unique_counts[i] = len(pids)
    return tap_counts, unique_counts


def _mean_max_per_second(
    centers_ms: np.ndarray,
    counts: np.ndarray,
    t0_ms: float,
    t1_ms: float,
) -> float:
    maxes = []
    sec_edges = np.arange(t0_ms, t1_ms + 1e-9, 1000.0)
    for lo, hi in zip(sec_edges[:-1], sec_edges[1:]):
        mask = (centers_ms >= lo) & (centers_ms < hi)
        if mask.any():
            maxes.append(float(np.max(counts[mask])))
    return float(np.mean(maxes)) if maxes else np.nan


def istc_table(
    df: pd.DataFrame,
    bin_ms: float,
    step_ms: float,
    t0_s: float | None,
    t1_s: float | None,
    alignment_offsets: dict[str, float],
) -> pd.DataFrame:
    """GlobalTap/Granot-style ISTC: unique participants in 100 ms bins.

    For each excerpt, slide a bin in step_ms increments, count unique
    participants with at least one tap in each bin, take the maximum count within
    each 1 s window, then average those maxima.
    """
    rows = []
    for stim, sub in df.groupby("stim_name"):
        participant_taps = _tap_participant_arrays(sub, alignment_offsets)
        if not participant_taps:
            continue
        all_taps = np.concatenate([arr for _, arr in participant_taps])
        lo = t0_s * 1000.0 if t0_s is not None else float(np.nanmin(all_taps))
        hi = t1_s * 1000.0 if t1_s is not None else float(np.nanmax(all_taps))
        centers = np.arange(lo, hi + step_ms, step_ms)
        tap_counts, unique_counts = _participant_bin_counts(participant_taps, centers, bin_ms)
        rows.append({
            "stim_name": stim,
            "istc_mean_max_unique_per_sec": _mean_max_per_second(centers, unique_counts, lo, hi),
            "tap_count_mean_max_per_sec": _mean_max_per_second(centers, tap_counts, lo, hi),
            "max_tap_count_per_100ms_bin": int(np.max(tap_counts)),
            "max_unique_participants_per_100ms_bin": int(np.max(unique_counts)),
            "mean_tap_count_per_100ms_bin": float(np.mean(tap_counts)),
            "mean_unique_participants_per_100ms_bin": float(np.mean(unique_counts)),
            "n_participants": int(sub["participant_uid"].nunique() if "participant_uid" in sub else sub["participant_id"].nunique()),
            "n_trials": int(len(sub)),
            "bin_ms": bin_ms,
            "step_ms": step_ms,
            "window_t0_s": lo / 1000.0,
            "window_t1_s": hi / 1000.0,
        })
    return pd.DataFrame(rows)


def time_resolved_istc_table(
    df: pd.DataFrame,
    bin_ms: float,
    step_ms: float,
    window_s: float,
    hop_s: float,
    t0_s: float | None,
    t1_s: float | None,
    alignment_offsets: dict[str, float],
) -> pd.DataFrame:
    """Sliding-window ISTC for precise correlations with MIR/neural traces."""
    rows = []
    for stim, sub in df.groupby("stim_name"):
        participant_taps = _tap_participant_arrays(sub, alignment_offsets)
        if not participant_taps:
            continue
        all_taps = np.concatenate([arr for _, arr in participant_taps]) / 1000.0
        start = t0_s if t0_s is not None else max(0.0, float(np.nanmin(all_taps)))
        stop = t1_s if t1_s is not None else float(np.nanmax(all_taps))
        starts = np.arange(start, max(start, stop - window_s) + 1e-9, hop_s)
        for w0 in starts:
            w1 = w0 + window_s
            centers = np.arange(w0 * 1000.0, w1 * 1000.0 + step_ms, step_ms)
            tap_counts, unique_counts = _participant_bin_counts(participant_taps, centers, bin_ms)
            rows.append({
                "stim_name": stim,
                "window_start_s": float(w0),
                "window_end_s": float(w1),
                "window_center_s": float((w0 + w1) / 2.0),
                "istc_mean_max_unique_per_sec": _mean_max_per_second(
                    centers, unique_counts, w0 * 1000.0, w1 * 1000.0
                ),
                "tap_count_mean_max_per_sec": _mean_max_per_second(
                    centers, tap_counts, w0 * 1000.0, w1 * 1000.0
                ),
                "max_unique_participants_per_100ms_bin": int(np.max(unique_counts)) if unique_counts.size else 0,
                "max_tap_count_per_100ms_bin": int(np.max(tap_counts)) if tap_counts.size else 0,
                "n_participants": int(sub["participant_uid"].nunique() if "participant_uid" in sub else sub["participant_id"].nunique()),
            })
    return pd.DataFrame(rows)


def ioi_ratio_table(trial_df: pd.DataFrame, consensus_summary: pd.DataFrame) -> pd.DataFrame:
    con = consensus_summary[["stim_name", "consensus_median_ioi_s"]].copy()
    merged = trial_df.merge(con, on="stim_name", how="left")
    merged["participant_ioi_to_consensus_ioi_ratio"] = (
        merged["mean_ioi_s"] / merged["consensus_median_ioi_s"]
    )
    return merged[
        [
            "trial_row",
            "stim_name",
            "participant_uid",
            "mean_ioi_s",
            "consensus_median_ioi_s",
            "participant_ioi_to_consensus_ioi_ratio",
            "perceived_tempo_bpm",
            "cv_ioi_pct",
        ]
    ]


def write_summary(out_dir: Path, trial_df: pd.DataFrame, consensus: pd.DataFrame, istc: pd.DataFrame) -> None:
    lines = [
        "# Bach Tapping Metrics Summary",
        "",
        f"- Trials analyzed: {len(trial_df)}",
        f"- Stimuli analyzed: {trial_df['stim_name'].nunique() if not trial_df.empty else 0}",
        f"- Median trial CV IOI: {trial_df['trial_cv_ioi_pct'].median():.3f}%" if not trial_df.empty else "- Median trial CV IOI: n/a",
        f"- Median consensus beat-sequence CV IOI: {consensus['beat_sequence_cv_ioi_pct'].median():.3f}%" if not consensus.empty else "- Median consensus beat-sequence CV IOI: n/a",
        f"- Median consensus tempo: {consensus['consensus_tempo_bpm'].median():.3f} BPM" if not consensus.empty else "- Median consensus tempo: n/a",
        "",
        "Outputs:",
        "- `trial_ioi_metrics.csv`",
        "- `kde_consensus_peaks.csv`",
        "- `track_consensus_summary.csv`",
        "- `istc_per_track.csv`",
        "- `istc_time_resolved.csv`",
        "- `ioi_ratio_per_trial.csv`",
    ]
    if not istc.empty:
        top = istc.sort_values("istc_mean_max_unique_per_sec", ascending=False).head(5)
        lines.extend(["", "## Highest Temporal Coherence Tracks", "", "| stim_name | ISTC mean max unique / sec |", "|---|---:|"])
        for _, row in top.iterrows():
            lines.append(f"| {row['stim_name']} | {row['istc_mean_max_unique_per_sec']:.3f} |")
    (out_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-csv", default=str(DEFAULT_INPUT))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--alignment-manifest", default=str(DEFAULT_MANIFEST))
    ap.add_argument("--t0", type=float, default=None)
    ap.add_argument("--t1", type=float, default=None)
    ap.add_argument("--kde-bandwidth-ms", type=float, default=80.0)
    ap.add_argument("--kde-dt-ms", type=float, default=5.0)
    ap.add_argument("--peak-distance-ms", type=float, default=150.0)
    ap.add_argument("--peak-prominence-frac", type=float, default=0.10)
    ap.add_argument("--bin-ms", type=float, default=100.0)
    ap.add_argument("--step-ms", type=float, default=50.0)
    ap.add_argument("--time-window-s", type=float, default=1.0)
    ap.add_argument("--time-hop-s", type=float, default=0.25)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.input_csv, low_memory=False)
    if "usable" in df.columns:
        df = df[df["usable"].fillna(False).astype(bool)].copy()
    elif "failed" in df.columns:
        df = df[~df["failed"].fillna(False).astype(bool)].copy()

    alignment_offsets = load_alignment_offsets(Path(args.alignment_manifest))
    trial_df, arrays = trial_metrics(df, args.t0, args.t1, alignment_offsets)
    peaks, consensus = consensus_tables(
        arrays,
        bandwidth_s=args.kde_bandwidth_ms / 1000.0,
        dt_s=args.kde_dt_ms / 1000.0,
        min_peak_distance_s=args.peak_distance_ms / 1000.0,
        prominence_frac=args.peak_prominence_frac,
    )
    istc = istc_table(df, args.bin_ms, args.step_ms, args.t0, args.t1, alignment_offsets)
    istc_time = time_resolved_istc_table(
        df,
        args.bin_ms,
        args.step_ms,
        args.time_window_s,
        args.time_hop_s,
        args.t0,
        args.t1,
        alignment_offsets,
    )
    ratios = ioi_ratio_table(trial_df, consensus)

    trial_df.to_csv(out_dir / "trial_ioi_metrics.csv", index=False)
    peaks.to_csv(out_dir / "kde_consensus_peaks.csv", index=False)
    consensus.to_csv(out_dir / "track_consensus_summary.csv", index=False)
    istc.to_csv(out_dir / "istc_per_track.csv", index=False)
    istc_time.to_csv(out_dir / "istc_time_resolved.csv", index=False)
    ratios.to_csv(out_dir / "ioi_ratio_per_trial.csv", index=False)
    write_summary(out_dir, trial_df, consensus, istc)
    print(f"Wrote Bach tapping metrics to {out_dir}")


if __name__ == "__main__":
    main()
