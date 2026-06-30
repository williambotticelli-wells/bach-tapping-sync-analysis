#!/usr/bin/env python3
"""Build a beta-table MIDI sync draft.

This is the same alignment workflow as the frozen sync draft, but the MIDI
source is selected from beta_table.csv and alltracks-midi:

    alltracks-midi/<piece>_<oname_midi>

Source deployed/matched WAVs and onset values come from the existing frozen
sync draft so this can be compared directly against the prior candidate-MIDI
alignment.
"""

from __future__ import annotations

import csv
import re
import sys
import wave
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_three_file_sync_packet import render_midi_piano, wav_duration  # noqa: E402
from build_track10_23_corrections import estimate_onset_s, plot_stacked  # noqa: E402


BACH_ROOT = SCRIPT_DIR.parents[0]
BETA_TABLE = BACH_ROOT / "beta_table.csv"
FROZEN_MANIFEST = BACH_ROOT / "alignment" / "frozen_sync_draft" / "bach_frozen_sync_manifest_draft.csv"
DEPLOYED_REVIEW = BACH_ROOT / "alignment" / "deployed_listening_packet" / "deployed_listening_review.csv"
MIDI_ROOT = BACH_ROOT / "alltracks-midi"
OUT_ROOT = BACH_ROOT / "alignment" / "beta_midi_sync_draft"

# The deployed folder contains two duplicate-basename stimuli with " 2.wav".
# beta_table.csv omits the " 2" suffix, so these must be assigned to the
# alternate beta rows explicitly rather than normalized onto their non-"2"
# siblings.
BETA_PIECE_OVERRIDES = {
    "track8": "wtc1f03",
    "track9": "wtc1f03",
}


def normalize_deployed_name(path_or_name: str) -> str:
    """Map deployed duplicates like `name 2.wav` back to `name.wav`."""
    name = Path(str(path_or_name)).name
    return re.sub(r" ([0-9]+)(?=\.wav$)", "", name, flags=re.IGNORECASE)


def crop_wav(source: Path, dest: Path, start_s: float) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(source), "rb") as wf:
        sr = wf.getframerate()
        start_frame = max(0, int(round(start_s * sr)))
        wf.setpos(min(start_frame, wf.getnframes()))
        frames = wf.readframes(wf.getnframes() - wf.tell())
        params = wf.getparams()
    with wave.open(str(dest), "wb") as out:
        out.setparams(params)
        out.writeframes(frames)


def load_beta_lookup() -> dict[tuple[str, str], pd.Series]:
    beta = pd.read_csv(BETA_TABLE, dtype=str).fillna("")
    lookup: dict[tuple[str, str], pd.Series] = {}
    for _, row in beta.iterrows():
        lookup[(row["piece"], row["oname"])] = row
    return lookup


def load_original_deployed_names() -> dict[str, str]:
    review = pd.read_csv(DEPLOYED_REVIEW, dtype=str).fillna("")
    names: dict[str, str] = {}
    for _, row in review.iterrows():
        # Each stim has one deployed filename in practice; duplicated beta joins
        # are resolved later by the frozen manifest's WTC code.
        names.setdefault(row["stim_name"], row["deployed_filename"])
    return names


def main() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    aligned_root = OUT_ROOT / "aligned_audio_t0"
    manifest = pd.read_csv(FROZEN_MANIFEST, dtype=str).fillna("")
    beta_lookup = load_beta_lookup()
    original_deployed_names = load_original_deployed_names()

    rows: list[dict[str, object]] = []
    missing: list[str] = []

    for _, row in manifest.iterrows():
        track = row["stim_name"]
        manifest_piece = row["wtc_code"]
        piece = BETA_PIECE_OVERRIDES.get(track, manifest_piece)
        deployed = Path(row["deployed_source_wav"])
        matched = Path(row["matched_source_wav"])
        onset_s = float(row["manual_onset_s"])
        deployed_name = normalize_deployed_name(original_deployed_names.get(track, deployed.name))
        beta_row = beta_lookup.get((piece, deployed_name))

        status = "beta_midi_draft_needs_manual_review"
        notes = str(row.get("notes", ""))
        midi_path: Path | None = None
        if beta_row is None:
            missing.append(f"{track}: no beta row for ({piece}, {deployed_name})")
            status = "missing_beta_row"
            oname_midi = ""
        else:
            oname_midi = beta_row["oname_midi"]
            midi_path = MIDI_ROOT / f"{piece}_{oname_midi}"
            if not midi_path.exists():
                missing.append(f"{track}: missing MIDI {midi_path}")
                status = "missing_beta_midi"

        out_dir = aligned_root / track
        out_dir.mkdir(parents=True, exist_ok=True)

        deployed_t0 = out_dir / "01_deployed_t0.wav"
        matched_t0 = out_dir / "02_matched_t0.wav"
        midi_full = out_dir / "03_beta_midi_rendered_full.wav"
        midi_t0 = out_dir / "03_beta_midi_piano_t0.wav"
        plot_path = out_dir / f"{track}_beta_midi_t0_stacked_check.png"

        crop_wav(deployed, deployed_t0, onset_s)
        crop_wav(matched, matched_t0, onset_s)

        midi_render_ok = False
        midi_render_error = ""
        if midi_path is not None and midi_path.exists():
            midi_render_ok, midi_render_error = render_midi_piano(
                midi_path,
                midi_full,
                wav_duration(deployed),
                onset_s,
            )
            if midi_render_ok:
                crop_wav(midi_full, midi_t0, onset_s)
                plot_stacked(
                    track,
                    [
                        ("deployed_t0", deployed_t0),
                        ("matched_t0", matched_t0),
                        ("beta_midi_t0", midi_t0),
                    ],
                    0.0,
                    plot_path,
                )
            else:
                status = "beta_midi_render_failed"
                missing.append(f"{track}: render failed for {midi_path}: {midi_render_error}")

        rows.append({
            "stim_name": track,
            "wtc_code": piece,
            "manifest_wtc_code": manifest_piece,
            "beta_piece_override_applied": piece != manifest_piece,
            "deployed_basename_normalized": deployed_name,
            "beta_oname": "" if beta_row is None else beta_row["oname"],
            "beta_oname_midi": oname_midi,
            "beta_list": "" if beta_row is None else beta_row["list"],
            "beta_perf": "" if beta_row is None else beta_row["beta_perf"],
            "beta_score": "" if beta_row is None else beta_row["beta_score"],
            "manual_onset_s": onset_s,
            "onset_source": row["onset_source"],
            "deployed_source_wav": str(deployed),
            "matched_source_wav": str(matched),
            "beta_midi_path": str(midi_path) if midi_path is not None else "",
            "deployed_t0_wav": str(deployed_t0),
            "matched_t0_wav": str(matched_t0),
            "beta_midi_t0_wav": str(midi_t0) if midi_t0.exists() else "",
            "post_crop_t0_plot": str(plot_path) if plot_path.exists() else "",
            "deployed_source_duration_s": wav_duration(deployed),
            "deployed_t0_duration_s": wav_duration(deployed_t0),
            "matched_t0_duration_s": wav_duration(matched_t0),
            "beta_midi_t0_duration_s": wav_duration(midi_t0) if midi_t0.exists() else "",
            "deployed_t0_auto_onset_s": estimate_onset_s(deployed_t0),
            "matched_t0_auto_onset_s": estimate_onset_s(matched_t0),
            "beta_midi_t0_auto_onset_s": estimate_onset_s(midi_t0) if midi_t0.exists() else "",
            "sync_status": status,
            "midi_render_ok": midi_render_ok,
            "midi_render_error": midi_render_error,
            "prior_sync_status": row["sync_status"],
            "notes": notes,
        })

    manifest_path = OUT_ROOT / "bach_beta_midi_sync_manifest.csv"
    with manifest_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    readme = OUT_ROOT / "README.md"
    readme.write_text(
        "# Bach Beta MIDI Sync Draft\n\n"
        "This folder rebuilds the same t=0 aligned checks as the frozen sync draft,\n"
        "but selects MIDI files from `beta_table.csv` and `alltracks-midi` using\n"
        "`alltracks-midi/<piece>_<oname_midi>`.\n\n"
        "Review `bach_beta_midi_sync_manifest.csv` and the per-track stacked plots in\n"
        "`aligned_audio_t0/<track>/` before treating this as final.\n"
    )

    print(f"Wrote beta MIDI sync draft to {OUT_ROOT}")
    if missing:
        print("Issues:")
        for item in missing:
            print(f"- {item}")


if __name__ == "__main__":
    main()
