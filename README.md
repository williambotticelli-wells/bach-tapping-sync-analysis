# Bach Tapping Sync + MIR/MIDI Analysis Handoff

Curated Rena/Nori-facing handoff for the Bach tapping, stimulus-sync,
MIRToolbox, MIDI Toolbox, and exploratory GlobalTap-style analyses.

## What To Review First

1. Confirm piece mapping for `track8`, `track9`, `track10`, and `track23`.
   See `docs/handoff_remaining_gates_resolution.md` and
   `tables/analysis__handoff_resolution__beta_table_vs_manifest_piece_mismatches.csv`.
2. Listen to canonical optimizer click previews and mark the checklist in
   `tables/analysis__handoff_resolution__optimizer_click_qc_manifest.csv`.
3. Review the main time-binned analysis matrix:
   `tables/analysis__beta_sync_multimodal__bach_time_binned_multimodal_with_matlab_toolboxes.csv`.
4. Treat all correlation outputs as exploratory screens, not final paper-level
   inference.

## Timing convention

All time-resolved files use stimulus-relative time where `t=0` is the first musical onset in the beta-sync draft. Please verify that this `t=0` matches the audio/ECoG timing convention before running neural models.

## Folder contents

- `audio_midi_t0/`: one folder per track with aligned deployed audio, matched audio, rendered MIDI audio, original MIDI, and stacked sync plot.
- `audio_midi_payload_manifest.csv`: per-track payload manifest and sync caveats.
- `tables/`: curated analysis CSVs copied from the Bach analysis pipeline.
- `code/`: scripts used to build sync analysis tables, MATLAB MIR/MIDI features, and hypothesis screens.
- `docs/`: concise handoff/status notes.
- `plots/`: PNG summaries of the strongest within-track feature/coherence associations.

## Most important tables

- `tables/bach_beta_midi_sync_manifest.csv`: canonical sync manifest.
- `tables/analysis__beta_sync_multimodal__bach_time_binned_multimodal_with_matlab_toolboxes.csv`: main time-binned analysis matrix.
- `tables/analysis__matlab_toolbox_features__matlab_toolbox_feature_inventory.csv`: list of available feature sets.
- `tables/analysis__beta_sync_tapping__istc_per_track.csv`: per-track tapping coherence.
- `tables/analysis__beta_sync_tapping__istc_time_resolved.csv`: time-resolved tapping coherence.
- `tables/analysis__beta_sync_hypotheses__feature_coherence_correlations.csv`: first-pass time-binned correlations.
- `tables/analysis__beta_sync_hypotheses__nori_whole_piece_top_correlations.csv`: first-pass whole-piece Nori/MIR correlations.
- `tables/analysis__beta_globaltap_canonical__bach_globaltap_style_track_summary.csv`: canonical GlobalTap optimizer summary for Bach.
- `tables/analysis__beta_globaltap_canonical__split_half_reliability_first30s.csv`: first-30s split-half reliability.
- `tables/analysis__beta_globaltap_canonical__convergence_to_full_density_first30s.csv`: participant-count convergence screen.
- `tables/analysis__beta_globaltap_canonical__optimizer_whole_piece_feature_correlations.csv`: optimizer-stage metrics vs whole-piece MIR/MIDI features.
- `tables/analysis__beta_globaltap_canonical__optimizer_time_binned_within_track_correlations.csv`: local optimizer/tapping metrics vs time-binned MIR/MIDI features, centered within track.
- `tables/analysis__handoff_resolution__corpus_mapping_audit.csv`: final-vs-beta piece mapping audit.
- `tables/analysis__handoff_resolution__optimizer_click_qc_manifest.csv`: manual click-preview QC checklist.

## Current caveats

- The source `beta_table.csv` has 24 rows and 10 WTC codes. Do not describe this
  as 12 unique pieces x 2 performances unless Rena/Nori provides a different
  grouping.
- Mapping confirmation is specifically needed for `track8`, `track9`, `track10`,
  and `track23`.
- The feature/coherence correlations are exploratory screens. They should be followed by mixed/permutation models before paper-level claims.
- Participant-level trial tables are redacted by default: participant identifiers and source audio filenames are not included in this packet.
- The canonical GlobalTap optimized beat-grid / split-half / convergence stack is included as exploratory QC/context.
- MIDI-onset F-measure is an event/synchronization diagnostic, not true beat-tracker F1. True beat F1 would require reference beat annotations or algorithm beat predictions on this same `t=0` clock.
- Emotion-slider and ECoG data are not included here; the schema placeholders are in the source repo under `analysis/future_emotion_neuro_schema/`.

## Preliminary signal

Across time bins, denser/active MIDI texture tends to coincide with higher tapping concentration, while broader/brighter spectral texture tends to coincide with lower tapping concentration. This is consistent across four time-resolved tapping targets but should be treated as exploratory.
