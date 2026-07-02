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

## Most important tables

- `tables/bach_beta_midi_sync_manifest.csv`: canonical sync manifest.
- `tables/analysis__beta_sync_multimodal__bach_time_binned_multimodal_with_matlab_toolboxes.csv`: main time-binned analysis matrix.
- `tables/analysis__beta_sync_100ms__bach_100ms_midi_tapping_feature_vectors.csv`: 100 ms MIDI and tapping feature vectors for emotion/ECoG joins.
- `tables/analysis__beta_sync_100ms_models__bach_100ms_within_track_correlations.csv`: 100 ms within-track MIDI/tapping correlation screen with redundant fixed-bin rescalings omitted.
- `tables/analysis__beta_sync_100ms_models__bach_100ms_within_track_bayesian_ridge_screen.csv`: Bayesian ridge direction screen for the 100 ms MIDI/tapping vectors.
- `tables/analysis__matlab_toolbox_features__matlab_toolbox_feature_inventory.csv`: list of available feature sets.
- `tables/analysis__beta_sync_tapping__istc_per_track.csv`: per-track tapping coherence.
- `tables/analysis__beta_sync_tapping__istc_time_resolved.csv`: time-resolved tapping coherence.
- `tables/analysis__beta_sync_hypotheses__feature_coherence_correlations.csv`: time-binned feature/coherence screen for the representative tapping-concentration target.
- `tables/analysis__beta_sync_hypotheses__whole_piece_mir_top_correlations.csv`: whole-piece MIR feature/coherence screens.
- `tables/analysis__beta_globaltap_canonical__bach_globaltap_style_track_summary.csv`: exploratory GlobalTap-style optimizer summary for Bach.
- `tables/analysis__beta_globaltap_canonical__split_half_reliability_first30s.csv`: first-30s split-half reliability.
- `tables/analysis__beta_globaltap_canonical__convergence_to_full_density_first30s.csv`: participant-count convergence screen.
- `tables/analysis__beta_globaltap_canonical__optimizer_whole_piece_feature_correlations.csv`: optimizer-stage metrics vs whole-piece MIR/MIDI features.
- `tables/analysis__beta_globaltap_canonical__optimizer_time_binned_within_track_correlations.csv`: local optimizer/tapping metrics vs time-binned MIR/MIDI features, centered within track.
- `tables/piece_mapping_notes.csv`: concise notes for tracks with piece-code corrections or mapping ambiguity.

## Notes

- The source stimulus table contains 24 rows and 10 WTC piece codes.
- Participant-level trial tables are redacted by default: participant identifiers and source audio filenames are not included.
- The GlobalTap-style optimizer outputs are included as exploratory context and quality-control material.
- MIDI-onset agreement is a synchronization/event diagnostic, not true beat-tracker F1.
- Redundant tapping-count targets and fixed-bin density rescalings were removed from the screening outputs; use `istc_mean_max_unique_per_sec` for the main time-binned tapping-concentration screen and `tap_count_100ms` for the 100 ms vector screen.
- Emotion-slider and ECoG data are not included in this repository.

## Preliminary signal

Across time bins, denser/active MIDI texture tends to coincide with higher tapping concentration, while broader/brighter spectral texture tends to coincide with lower tapping concentration. This is based on a representative tapping-concentration target and should be treated as exploratory.

At the 100 ms MIDI/tapping resolution, the strongest within-track associations are positive but small: active-note count and MIDI onset count track local tap concentration. These vectors are best treated as alignment-ready inputs for emotion/ECoG models.
