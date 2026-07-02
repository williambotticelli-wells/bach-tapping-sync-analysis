# Bach Tapping Sync + MIR/MIDI Analysis

This repository contains synchronized Bach audio/MIDI materials, tapping
coherence analyses, MIRToolbox/MIDI Toolbox features, and preliminary
feature/coherence results.

## Timing convention

All time-resolved files use stimulus-relative time where `t=0` is the first
musical onset in the synchronized audio/MIDI packet.

## Folder contents

- `audio_midi_t0/`: one folder per track with aligned deployed audio, matched audio, rendered MIDI audio, original MIDI, and stacked sync plot.
- `audio_midi_payload_manifest.csv`: per-track payload manifest and sync caveats.
- `tables/`: analysis CSVs.
- `code/`: scripts used to build sync analysis tables, MATLAB MIR/MIDI features, and hypothesis screens.
- `docs/`: concise analysis notes and data guide.
- `plots/`: PNG summary of the strongest within-track feature/coherence association.

## Quick start

- If this checkout was cloned with Git LFS, run `git lfs pull` before opening
  audio, MIDI, or PNG files.
- Use `docs/data_guide.md` as the table index.
- Use `tables/analysis__beta_sync_100ms__bach_100ms_midi_tapping_feature_vectors.csv` for 100 ms emotion/ECoG joins.
- Use `tables/analysis__beta_sync_100ms__bach_100ms_audio_feature_vectors.csv` for 100 ms acoustic/MIR-style joins.
- Use `tables/analysis__beta_sync_100ms__bach_100ms_audio_midi_tapping_feature_vectors.csv` for the combined 100 ms acoustic/MIDI/tapping grid.
- Use `tables/analysis__beta_sync_multimodal__bach_time_binned_multimodal_with_matlab_toolboxes.csv` for time-binned MIR/MIDI/audio/tapping analyses.
- Use `audio_midi_t0/` when checking synchronized audio/MIDI materials by ear or by waveform.

The checked-in tables and synchronized assets are ready to use directly. The
scripts in `code/` document how the package was built and can be rerun from the
full Bach workspace layout; the GlobalTap optimizer script additionally expects
the companion optimizer repository next to the Bach workspace.

## Table Use

- 100 ms joins use `stim_name`, `wtc_code`, and `bin_center_s`.
- Time-binned joins use `stim_name`, `wtc_code`, and `window_center_s`.
- For local MIDI/tapping effects, start with the within-track screens. Global
  correlation tables are included as context and can reflect track-level
  differences.
- In optimizer tables, rows where `target == istc_mean_max_unique_per_sec`
  concern tapping concentration; rows with `optimizer_*` targets are optimizer
  quality-control screens.

## Most important tables

- `tables/bach_beta_midi_sync_manifest.csv`: canonical sync manifest.
- `tables/analysis__beta_sync_multimodal__bach_time_binned_multimodal_with_matlab_toolboxes.csv`: main time-binned analysis matrix.
- `tables/analysis__beta_sync_100ms__bach_100ms_midi_tapping_feature_vectors.csv`: 100 ms MIDI and tapping feature vectors for emotion/ECoG joins.
- `tables/analysis__beta_sync_100ms__bach_100ms_audio_feature_vectors.csv`: 100 ms acoustic feature vectors on the same grid.
- `tables/analysis__beta_sync_100ms__bach_100ms_audio_midi_tapping_feature_vectors.csv`: joined 100 ms acoustic/MIDI/tapping feature vectors.
- `tables/analysis__beta_sync_100ms_models__bach_100ms_audio_within_track_correlations.csv`: local 100 ms acoustic/tapping correlation screen.
- `tables/analysis__beta_sync_100ms_models__bach_100ms_within_track_correlations.csv`: local 100 ms MIDI/tapping correlation screen.
- `tables/analysis__beta_sync_100ms_models__bach_100ms_within_track_bayesian_ridge_screen.csv`: Bayesian ridge direction screen for the 100 ms MIDI/tapping vectors.
- `tables/analysis__matlab_toolbox_features__matlab_toolbox_feature_inventory.csv`: list of available feature sets.
- `tables/analysis__beta_sync_tapping__istc_per_track.csv`: per-track tapping coherence.
- `tables/analysis__beta_sync_tapping__istc_time_resolved.csv`: time-resolved tapping coherence.
- `tables/analysis__beta_sync_hypotheses__feature_coherence_correlations.csv`: time-binned feature/coherence screen.
- `tables/analysis__beta_sync_hypotheses__whole_piece_mir_top_correlations.csv`: whole-piece MIR feature/coherence screens.
- `tables/analysis__beta_globaltap_canonical__bach_globaltap_style_track_summary.csv`: exploratory GlobalTap-style optimizer summary for Bach.
- `tables/analysis__beta_globaltap_canonical__split_half_reliability_first30s.csv`: first-30s split-half reliability.
- `tables/analysis__beta_globaltap_canonical__convergence_to_full_density_first30s.csv`: participant-count convergence screen.
- `tables/analysis__beta_globaltap_canonical__optimizer_whole_piece_feature_correlations.csv`: optimizer-stage metrics vs whole-piece MIR/MIDI features.
- `tables/analysis__beta_globaltap_canonical__optimizer_time_binned_within_track_correlations.csv`: local optimizer and tapping metrics vs time-binned MIR/MIDI features, centered within track.
- `tables/piece_mapping_notes.csv`: concise notes for tracks with piece-code corrections or mapping ambiguity.

## Notes

- The source stimulus table contains 24 rows and 10 WTC piece codes.
- Participant-level trial tables are redacted by default: participant identifiers and source audio filenames are not included.
- The GlobalTap-style optimizer outputs are included as exploratory context and quality-control material.
- MIDI-onset agreement is a synchronization/event diagnostic, not true beat-tracker F1.
- Emotion-slider and ECoG data are not included in this repository.

## Preliminary signal

Across time bins, denser/active MIDI texture tends to coincide with higher tapping concentration, while broader/brighter spectral texture tends to coincide with lower tapping concentration. This should be treated as exploratory.

At the 100 ms MIDI/tapping resolution, the strongest within-track associations are positive but small: active-note count and MIDI onset count track local tap concentration. These vectors are best treated as alignment-ready inputs for emotion/ECoG models.
