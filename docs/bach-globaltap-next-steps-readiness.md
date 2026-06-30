# Bach And GlobalTap Next Steps Readiness

## Goal

Create a single first-onset-aligned timebase for:

- Bach MIDI files for the performed pieces.
- Collaborator B/Weston WAV files used for neural/ECoG patient tapping.
- Collective tapping WAV files used in the PsyNet/REPP Bach experiment.
- Participant tap times, MIR/audio features, and later neural signal traces.

The analysis clock is `t = 0` at the first musical onset. Original file-start
offsets remain in the manifest for provenance.

## Current Local Status

- Bach behavioral tap exports are present in
  `bach-tap-data/bach-tap/bach-tapping/bach-tapping-data`.
- Current derived tapping tables are present under
  `bach-tap-data/bach-tap/bach-tapping/bach-tapping-data/database/derived`.
- Experiment code expects the collective stimuli at
  `bach-tap-experiment-files/static/bach_pieces`.
- Both visible `static/bach_pieces` entries are symlinks to
  `../../analysis_pipeline/audio/bach_pieces`; in this checkout they need to be
  verified after the actual audio asset location is available.
- `maestro_files` now exposes local Bach WAV candidates under `bachwtc_short`
  and `loudnorm_resampled`; these are included in the generated manifest.
- The Weston code download is now present at `weston-music-selection-main 3`.
  It includes MATLAB code such as `get_aligned_audio.m`, `get_recordings.m`,
  `split_midi_movements.m`, and `maestro-v3.0.0.json`.
- The Weston code download includes `audio_midi_offsets.xlsx` and split MIDI
  candidates under `weston-matlab/maestro_midi/Bach+Johann`; each Bach stimulus
  now has a WTC-code-based MIDI candidate set.
- The MIRToolbox scripts in `for_zohar_scripts` are present, but the helper
  functions `get_values` and `get_value` are not in that folder.

## New Reproducible Artifacts

- `alignment/README.md` defines the alignment workspace.
- `scripts/build_bach_asset_inventory.py` inventories WAV/MIDI/offset assets and
  writes a gap audit.
- `scripts/build_bach_alignment_manifest.py` creates the canonical per-stimulus
  alignment manifest template.
- `scripts/align_bach_stimuli.py` estimates first audio/MIDI onsets and writes a
  verification table without modifying source files.
- `scripts/build_bach_midi_candidate_review.py` maps each stimulus WAV basename
  to the Weston offset spreadsheet, WTC piece code, and all matching split-MIDI
  candidates for manual confirmation. Duplicate copied WAV names such as
  `...wav--1 2.wav` are treated as the second matching Weston offset occurrence.
- `scripts/build_bach_sync_qa_packet.py` creates the manual synchronization QA
  packet: checklist, onset clips, onset plots, MIDI diagnostics, and, after
  `selected_midi_path` is filled, audio/MIDI overlays and stereo listen-check
  files.
- `scripts/compute_bach_tap_metrics.py` computes mean IOI, perceived tempo, CV
  IOI, KDE consensus peaks, ISTC-like coherence, and IOI ratios.
- `scripts/extract_bach_time_resolved_audio_features.py` extracts frame-wise
  audio features aligned to first musical onset for precise correlations.
- `../analysis/convergence/globaltap_convergence_power.py` implements empirical
  GlobalTap sample-size/convergence analysis.

## Metric Definitions To Use

- Participant tapping consistency: trial-level `sd(IOI) / mean(IOI) * 100`.
- GlobalTap beat-sequence CV: consensus beat-grid `sd(IOI) / mean(IOI)`, also
  exported as percent for readability.
- ISTC: unique participants per 100 ms bin, 50 ms step, max per 1 s window,
  then averaged over time.
- Time-resolved coherence: the same ISTC calculation repeated in sliding windows
  so it can be correlated with MIR, emotion, or neural/ECoG time series.

## Bach Analysis Sequence

1. Clone or attach the external aligned-WAV/MIDI repo and rerun the asset
   inventory with `--asset-root`.
2. Resolve the collective tapping symlink so the 24 Bach WAVs used in PsyNet are
   visible locally.
3. Build the alignment manifest and manually confirm the join key:
   `stim_name`, PsyNet `audio_filename`, collective WAV, Collaborator B WAV, MIDI, and any
   neural/ECoG identifiers.
4. Estimate first onsets for every WAV and MIDI file; review any onset spread
   greater than the tolerance.
5. Use `bach_midi_candidate_review.csv` to choose the exact MIDI split for each
   stimulus; WTC-code matching narrows each piece to a small candidate set.
6. Run `build_bach_sync_qa_packet.py` and complete
   `alignment/sync_qa_packet/manual_sync_checklist.csv` for all 24 stimuli.
7. Manually listen-check all 24 aligned pieces using the onset clips, overlays,
   and stereo listen-check files.
8. Freeze a verified manifest before correlating MIR, tapping, or neural data.
9. Compute frame-wise MIR/audio features and sliding-window coherence on the
   frozen first-onset timebase.

## Analysis Gate

Current Bach behavioral, MIR, and future ECoG correlations should be considered
exploratory until all 24 rows in
`alignment/sync_qa_packet/manual_sync_checklist.csv` have
`ready_for_analysis=true`. That row should only be set after filename matching,
first-onset offset review, exact MIDI selection, audio/MIDI overlay inspection,
and human listen-checking all pass.

## Behavioral And Neural-Ready Metrics

The first behavioral outputs should include:

- Trial-level mean IOI and perceived tempo.
- Trial-level CV IOI as tapping consistency.
- Per-track KDE peak times as consensus beat locations.
- Per-track max unique participant count in 100 ms bins as temporal coherence.
- Participant IOI / consensus IOI ratios for tempo alignment.
- Sliding-window versions of coherence for correlation with MIR and neural data.

## GlobalTap Benchmark Questions

Use the new convergence script and existing GlobalTap pipeline outputs to answer:

- How many tappers are needed before consensus peaks stabilize?
- Does required N differ by country panel, corpus, tempo, or tap consistency?
- Where do madmom/other beat trackers agree or fail relative to human peaks?
- Are failures driven by low ISTC, high IOI CV, multimodal tapping, half/double
  tempo interpretations, or structurally ambiguous excerpts?

## Remaining Required Inputs

- Confirmation of the exact 24 collective tapping WAVs and their symlink target.
- Manual selection of the exact MIDI candidate for each of the 24 stimuli.
- Completed sync QA checklist with all rows marked `ready_for_analysis=true`.
- Missing MIR helper functions or a complete copy of Researcher B/Collaborator C's script bundle.
- Stable metadata table joining Bach piece/performance IDs across all modalities.
