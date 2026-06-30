#!/usr/bin/env python3
"""Build beta-sync Bach analysis tables.

This driver uses the corrected beta MIDI sync manifest as the canonical
alignment source and writes analysis-ready tables for:

- time-resolved audio features
- time-resolved MIDI features
- tapping metrics and time-resolved coherence
- joined multimodal time-window tables
- same-piece/performance summaries
- future emotion/neuro join schemas
"""

from __future__ import annotations

import csv
import hashlib
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_three_file_sync_packet import parse_midi_note_events  # noqa: E402
from compute_bach_tap_metrics import (  # noqa: E402
    consensus_tables,
    ioi_ratio_table,
    istc_table,
    time_resolved_istc_table,
    trial_metrics,
)
from extract_bach_time_resolved_audio_features import extract_features  # noqa: E402


BACH_ROOT = SCRIPT_DIR.parents[0]
MANIFEST = BACH_ROOT / "alignment" / "beta_midi_sync_draft" / "bach_beta_midi_sync_manifest.csv"
REUSE_AUDIT = BACH_ROOT / "alignment" / "beta_midi_sync_draft" / "beta_sync_file_reuse_audit.csv"
TAP_INPUT = (
    BACH_ROOT
    / "bach-tap-data/bach-tap/bach-tapping/bach-tapping-data/database/derived/"
    "tap_all_trials_combined_usable.csv"
)
OUT_ROOT = BACH_ROOT / "analysis"
SYNC_OUT = OUT_ROOT / "beta_sync_source"
FEATURE_OUT = OUT_ROOT / "beta_sync_features"
TAPPING_OUT = OUT_ROOT / "beta_sync_tapping"
MULTIMODAL_OUT = OUT_ROOT / "beta_sync_multimodal"
SCHEMA_OUT = OUT_ROOT / "future_emotion_neuro_schema"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> pd.DataFrame:
    manifest = pd.read_csv(MANIFEST, dtype=str).fillna("")
    required = [
        "stim_name",
        "wtc_code",
        "manual_onset_s",
        "deployed_t0_wav",
        "matched_t0_wav",
        "beta_midi_path",
        "beta_midi_t0_wav",
    ]
    missing = [col for col in required if col not in manifest.columns]
    if missing:
        raise RuntimeError(f"Beta sync manifest missing required columns: {missing}")
    return manifest


def freeze_sync_source(manifest: pd.DataFrame) -> None:
    SYNC_OUT.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MANIFEST, SYNC_OUT / "canonical_bach_beta_midi_sync_manifest.csv")
    if REUSE_AUDIT.exists():
        shutil.copy2(REUSE_AUDIT, SYNC_OUT / "canonical_beta_sync_file_reuse_audit.csv")

    rows = []
    for _, row in manifest.iterrows():
        deployed = Path(row["deployed_t0_wav"])
        matched = Path(row["matched_t0_wav"])
        midi = Path(row["beta_midi_path"])
        rows.append({
            "stim_name": row["stim_name"],
            "wtc_code": row["wtc_code"],
            "manifest_wtc_code": row.get("manifest_wtc_code", ""),
            "beta_piece_override_applied": row.get("beta_piece_override_applied", ""),
            "manual_onset_s": row["manual_onset_s"],
            "deployed_t0_wav": str(deployed),
            "matched_t0_wav": str(matched),
            "beta_midi_path": str(midi),
            "deployed_t0_sha256": sha256(deployed) if deployed.exists() else "",
            "matched_t0_sha256": sha256(matched) if matched.exists() else "",
            "beta_midi_sha256": sha256(midi) if midi.exists() else "",
        })
    pd.DataFrame(rows).to_csv(SYNC_OUT / "canonical_source_hashes.csv", index=False)


def time_windows(duration_s: float, window_s: float, hop_s: float) -> pd.DataFrame:
    starts = np.arange(0.0, max(0.0, duration_s - window_s) + 1e-9, hop_s)
    if starts.size == 0:
        starts = np.array([0.0])
    return pd.DataFrame({
        "window_start_s": starts,
        "window_end_s": starts + window_s,
        "window_center_s": starts + window_s / 2.0,
    })


def summarize_in_windows(
    frame_df: pd.DataFrame,
    value_cols: list[str],
    duration_s: float,
    window_s: float,
    hop_s: float,
) -> pd.DataFrame:
    windows = time_windows(duration_s, window_s, hop_s)
    rows = []
    for _, win in windows.iterrows():
        sub = frame_df[
            (frame_df["time_s_aligned"] >= win["window_start_s"])
            & (frame_df["time_s_aligned"] < win["window_end_s"])
        ]
        out = win.to_dict()
        out["n_frames"] = int(len(sub))
        for col in value_cols:
            vals = pd.to_numeric(sub[col], errors="coerce") if col in sub else pd.Series(dtype=float)
            out[f"{col}_mean"] = float(vals.mean()) if vals.notna().any() else np.nan
            out[f"{col}_std"] = float(vals.std(ddof=1)) if vals.notna().sum() > 1 else np.nan
        rows.append(out)
    return pd.DataFrame(rows)


def build_audio_features(manifest: pd.DataFrame, window_s: float, hop_s: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    FEATURE_OUT.mkdir(parents=True, exist_ok=True)
    frame_tables = []
    window_tables = []
    value_cols = [
        "rms",
        "spectral_centroid_hz",
        "spectral_bandwidth_hz",
        "spectral_rolloff_hz",
        "zero_crossing_rate",
        "onset_strength",
        "chroma_strength_mean",
    ]
    for _, row in manifest.iterrows():
        path = Path(row["deployed_t0_wav"])
        if not path.exists():
            continue
        feats = extract_features(path, sr=22050, hop_length=551, frame_length=2205, hop_ms=25.0, frame_ms=100.0)
        if feats.empty:
            continue
        feats.insert(0, "stim_name", row["stim_name"])
        feats.insert(1, "wtc_code", row["wtc_code"])
        feats.insert(2, "audio_role", "deployed_t0")
        feats.insert(3, "source_audio_path", str(path))
        feats["time_s_aligned"] = feats["time_s_file"]
        frame_tables.append(feats)

        duration = float(row.get("deployed_t0_duration_s", 0) or 0)
        win = summarize_in_windows(feats, value_cols, duration, window_s, hop_s)
        win.insert(0, "stim_name", row["stim_name"])
        win.insert(1, "wtc_code", row["wtc_code"])
        window_tables.append(win)

    frames = pd.concat(frame_tables, ignore_index=True) if frame_tables else pd.DataFrame()
    windows = pd.concat(window_tables, ignore_index=True) if window_tables else pd.DataFrame()
    frames.to_csv(FEATURE_OUT / "audio_features_framewise.csv", index=False)
    windows.to_csv(FEATURE_OUT / "audio_features_binned.csv", index=False)
    return frames, windows


def midi_event_table(row: pd.Series) -> pd.DataFrame:
    midi_path = Path(row["beta_midi_path"])
    if not midi_path.exists():
        return pd.DataFrame()
    notes = parse_midi_note_events(midi_path)
    if not notes:
        return pd.DataFrame()
    first_note = min(note[0] for note in notes)
    rows = []
    for start_s, end_s, pitch, velocity in notes:
        aligned_start = start_s - first_note
        aligned_end = max(aligned_start, end_s - first_note)
        rows.append({
            "stim_name": row["stim_name"],
            "wtc_code": row["wtc_code"],
            "midi_path": str(midi_path),
            "note_start_s_aligned": float(aligned_start),
            "note_end_s_aligned": float(aligned_end),
            "note_duration_s": float(max(0.0, aligned_end - aligned_start)),
            "pitch": int(pitch),
            "velocity": int(velocity),
        })
    return pd.DataFrame(rows)


def build_midi_features(manifest: pd.DataFrame, window_s: float, hop_s: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    event_tables = []
    window_tables = []
    for _, row in manifest.iterrows():
        events = midi_event_table(row)
        if events.empty:
            continue
        event_tables.append(events)
        duration = float(row.get("beta_midi_t0_duration_s", row.get("deployed_t0_duration_s", 0)) or 0)
        windows = time_windows(duration, window_s, hop_s)
        out_rows = []
        for _, win in windows.iterrows():
            sub = events[
                (events["note_start_s_aligned"] >= win["window_start_s"])
                & (events["note_start_s_aligned"] < win["window_end_s"])
            ]
            active = events[
                (events["note_start_s_aligned"] < win["window_end_s"])
                & (events["note_end_s_aligned"] > win["window_start_s"])
            ]
            starts = np.sort(sub["note_start_s_aligned"].to_numpy(dtype=float))
            iois = np.diff(starts)
            out = win.to_dict()
            out.update({
                "stim_name": row["stim_name"],
                "wtc_code": row["wtc_code"],
                "n_note_onsets": int(len(sub)),
                "note_onset_density_per_s": float(len(sub) / window_s) if window_s > 0 else np.nan,
                "mean_pitch": float(sub["pitch"].mean()) if len(sub) else np.nan,
                "std_pitch": float(sub["pitch"].std(ddof=1)) if len(sub) > 1 else np.nan,
                "mean_velocity": float(sub["velocity"].mean()) if len(sub) else np.nan,
                "mean_note_duration_s": float(sub["note_duration_s"].mean()) if len(sub) else np.nan,
                "mean_midi_ioi_s": float(np.mean(iois)) if iois.size else np.nan,
                "cv_midi_ioi": float(np.std(iois, ddof=1) / np.mean(iois)) if iois.size > 1 and np.mean(iois) > 0 else np.nan,
                "active_note_count": int(len(active)),
                "approx_polyphony": float(len(active) / max(1, len(sub))) if len(sub) else np.nan,
            })
            out_rows.append(out)
        window_tables.append(pd.DataFrame(out_rows))

    events = pd.concat(event_tables, ignore_index=True) if event_tables else pd.DataFrame()
    windows = pd.concat(window_tables, ignore_index=True) if window_tables else pd.DataFrame()
    events.to_csv(FEATURE_OUT / "midi_note_events_aligned.csv", index=False)
    windows.to_csv(FEATURE_OUT / "midi_features_binned.csv", index=False)
    return events, windows


def build_tapping_metrics(manifest: pd.DataFrame, window_s: float, hop_s: float) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    TAPPING_OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(TAP_INPUT, low_memory=False)
    if "usable" in df.columns:
        df = df[df["usable"].fillna(False).astype(bool)].copy()
    offsets = dict(zip(manifest["stim_name"], pd.to_numeric(manifest["manual_onset_s"], errors="coerce").fillna(0.0)))
    trial_df, arrays = trial_metrics(df, None, None, offsets)
    peaks, consensus = consensus_tables(arrays, bandwidth_s=0.080, dt_s=0.005, min_peak_distance_s=0.150, prominence_frac=0.10)
    istc = istc_table(df, bin_ms=100.0, step_ms=50.0, t0_s=None, t1_s=None, alignment_offsets=offsets)
    istc_time = time_resolved_istc_table(
        df,
        bin_ms=100.0,
        step_ms=50.0,
        window_s=window_s,
        hop_s=hop_s,
        t0_s=0.0,
        t1_s=None,
        alignment_offsets=offsets,
    )
    ratios = ioi_ratio_table(trial_df, consensus)

    meta_cols = ["stim_name", "wtc_code", "manifest_wtc_code", "beta_list", "beta_perf", "beta_score"]
    meta = manifest[[col for col in meta_cols if col in manifest.columns]].drop_duplicates("stim_name")
    for table, name in [
        (trial_df, "trial_ioi_metrics.csv"),
        (peaks, "kde_consensus_peaks.csv"),
        (consensus, "track_consensus_summary.csv"),
        (istc, "istc_per_track.csv"),
        (istc_time, "istc_time_resolved.csv"),
        (ratios, "ioi_ratio_per_trial.csv"),
    ]:
        if "stim_name" in table.columns:
            table = table.merge(meta, on="stim_name", how="left")
        table.to_csv(TAPPING_OUT / name, index=False)
    consensus_with_meta = consensus.merge(meta, on="stim_name", how="left")
    if not istc.empty:
        istc_cols = [
            "stim_name",
            "istc_mean_max_unique_per_sec",
            "tap_count_mean_max_per_sec",
            "max_tap_count_per_100ms_bin",
            "max_unique_participants_per_100ms_bin",
            "n_participants",
        ]
        consensus_with_meta = consensus_with_meta.merge(
            istc[[col for col in istc_cols if col in istc.columns]],
            on="stim_name",
            how="left",
        )
    return trial_df, consensus_with_meta, istc_time.merge(meta, on="stim_name", how="left")


def join_multimodal(audio_bins: pd.DataFrame, midi_bins: pd.DataFrame, istc_time: pd.DataFrame, consensus: pd.DataFrame) -> pd.DataFrame:
    MULTIMODAL_OUT.mkdir(parents=True, exist_ok=True)
    keys = ["stim_name", "wtc_code", "window_start_s", "window_end_s", "window_center_s"]
    joined = audio_bins.merge(midi_bins, on=keys, how="outer", suffixes=("_audio", "_midi"))
    if not istc_time.empty:
        istc_cols = [
            "stim_name",
            "window_start_s",
            "window_end_s",
            "window_center_s",
            "istc_mean_max_unique_per_sec",
            "tap_count_mean_max_per_sec",
            "max_unique_participants_per_100ms_bin",
            "max_tap_count_per_100ms_bin",
            "n_participants",
        ]
        joined = joined.merge(istc_time[[col for col in istc_cols if col in istc_time.columns]], on=["stim_name", "window_start_s", "window_end_s", "window_center_s"], how="left")
    if not consensus.empty:
        con_cols = [
            "stim_name",
            "n_trials",
            "n_consensus_peaks",
            "consensus_median_ioi_s",
            "beat_sequence_cv_ioi_pct",
            "consensus_tempo_bpm",
            "beta_perf",
            "beta_score",
            "beta_list",
            "manifest_wtc_code",
        ]
        joined = joined.merge(consensus[[col for col in con_cols if col in consensus.columns]], on="stim_name", how="left", suffixes=("", "_track"))
    joined.to_csv(MULTIMODAL_OUT / "bach_time_binned_multimodal_table.csv", index=False)
    return joined


def same_piece_summary(manifest: pd.DataFrame, consensus: pd.DataFrame, joined: pd.DataFrame) -> None:
    rows = []
    track_summary = consensus.copy()
    for piece, group in manifest.groupby("wtc_code"):
        stims = sorted(group["stim_name"].tolist())
        sub = track_summary[track_summary["stim_name"].isin(stims)]
        rows.append({
            "wtc_code": piece,
            "n_performances": len(stims),
            "stim_names": "|".join(stims),
            "beta_lists": "|".join(group.get("beta_list", pd.Series(dtype=str)).astype(str).tolist()),
            "beta_perf_values": "|".join(group.get("beta_perf", pd.Series(dtype=str)).astype(str).tolist()),
            "median_istc": float(sub["istc_mean_max_unique_per_sec"].median()) if "istc_mean_max_unique_per_sec" in sub and sub["istc_mean_max_unique_per_sec"].notna().any() else np.nan,
            "median_consensus_tempo_bpm": float(sub["consensus_tempo_bpm"].median()) if "consensus_tempo_bpm" in sub and sub["consensus_tempo_bpm"].notna().any() else np.nan,
            "tempo_range_bpm": float(sub["consensus_tempo_bpm"].max() - sub["consensus_tempo_bpm"].min()) if "consensus_tempo_bpm" in sub and sub["consensus_tempo_bpm"].notna().sum() > 1 else np.nan,
        })
    same_piece = pd.DataFrame(rows)
    same_piece.to_csv(MULTIMODAL_OUT / "same_piece_performance_summary.csv", index=False)

    if not joined.empty:
        feature_cols = [
            col for col in joined.columns
            if col.endswith("_mean") or col in {"note_onset_density_per_s", "istc_mean_max_unique_per_sec"}
        ]
        piece_windows = joined.groupby(["wtc_code", "window_center_s"], dropna=False)[feature_cols].mean(numeric_only=True).reset_index()
        piece_windows.to_csv(MULTIMODAL_OUT / "same_piece_window_feature_means.csv", index=False)


def write_future_schemas() -> None:
    SCHEMA_OUT.mkdir(parents=True, exist_ok=True)
    emotion_cols = [
        "stim_name",
        "wtc_code",
        "participant_id",
        "emotion_term",
        "window_start_s",
        "window_end_s",
        "window_center_s",
        "rating_mean",
        "rating_se",
        "n_ratings",
        "source_file",
    ]
    neuro_cols = [
        "subject_id",
        "stim_name",
        "wtc_code",
        "channel",
        "region",
        "neural_feature",
        "frequency_band",
        "window_start_s",
        "window_end_s",
        "window_center_s",
        "value",
        "source_file",
    ]
    pd.DataFrame(columns=emotion_cols).to_csv(SCHEMA_OUT / "emotion_time_resolved_schema.csv", index=False)
    pd.DataFrame(columns=neuro_cols).to_csv(SCHEMA_OUT / "neuro_ecog_time_resolved_schema.csv", index=False)
    (SCHEMA_OUT / "README.md").write_text(
        "# Future Emotion And Neuro Join Schemas\n\n"
        "These empty CSVs define the columns expected for later joins with the\n"
        "beta-sync multimodal table. Times should use the same `t=0` first musical\n"
        "onset clock as `bach_beta_midi_sync_manifest.csv`.\n"
    )


def write_summary(manifest: pd.DataFrame, audio_bins: pd.DataFrame, midi_bins: pd.DataFrame, joined: pd.DataFrame) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Bach Beta-Sync Analysis Outputs",
        "",
        f"- Canonical manifest rows: {len(manifest)}",
        f"- Audio feature windows: {len(audio_bins)}",
        f"- MIDI feature windows: {len(midi_bins)}",
        f"- Multimodal joined windows: {len(joined)}",
        "",
        "Canonical input:",
        "- `../alignment/beta_midi_sync_draft/bach_beta_midi_sync_manifest.csv`",
        "",
        "Output folders:",
        "- `beta_sync_source/`",
        "- `beta_sync_features/`",
        "- `beta_sync_tapping/`",
        "- `beta_sync_multimodal/`",
        "- `future_emotion_neuro_schema/`",
        "",
        "Notes:",
        "- `track7` and `track8` retain manual-onset QA notes; automated onset detection is not treated as authoritative for them.",
        "- Emotion and neuro tables are schemas only until those datasets are provided.",
    ]
    (OUT_ROOT / "README.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    window_s = 1.0
    hop_s = 0.25
    manifest = load_manifest()
    freeze_sync_source(manifest)
    audio_frames, audio_bins = build_audio_features(manifest, window_s, hop_s)
    midi_events, midi_bins = build_midi_features(manifest, window_s, hop_s)
    _, consensus, istc_time = build_tapping_metrics(manifest, window_s, hop_s)
    joined = join_multimodal(audio_bins, midi_bins, istc_time, consensus)
    same_piece_summary(manifest, consensus, joined)
    write_future_schemas()
    write_summary(manifest, audio_bins, midi_bins, joined)
    print(f"Wrote Bach beta-sync analyses to {OUT_ROOT}")


if __name__ == "__main__":
    main()
