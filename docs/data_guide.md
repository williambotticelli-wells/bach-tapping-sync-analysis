# Data Guide

## Synchronized Stimuli

- `audio_midi_t0/`: aligned deployed audio, matched audio, rendered MIDI audio,
  original MIDI, and sync plot for each track.
- `audio_midi_payload_manifest.csv`: file-level index for the synchronized
  materials.
- `tables/bach_beta_midi_sync_manifest.csv`: analysis manifest with timing and
  metadata.

## Main Analysis Tables

- `tables/analysis__beta_sync_multimodal__bach_time_binned_multimodal_with_matlab_toolboxes.csv`
  - Primary time-binned table for joining music features with tapping coherence.
    Join on `stim_name`, `wtc_code`, and `window_center_s`.
- `tables/analysis__beta_sync_100ms__bach_100ms_midi_tapping_feature_vectors.csv`
  - 100 ms feature-vector table for emotion/ECoG joins. Includes MIDI note onset
    count, active-note count, pitch min/max/range, velocity range, and tap count.
    Join on `stim_name`, `wtc_code`, and `bin_center_s`.
- `tables/analysis__beta_sync_100ms_models__bach_100ms_within_track_correlations.csv`
  - Within-track 100 ms correlation screen relating local MIDI features to local
    tap concentration.
- `tables/analysis__beta_sync_100ms_models__bach_100ms_within_track_bayesian_ridge_screen.csv`
  - Bayesian ridge direction screen using the same 100 ms feature vectors.
- `tables/analysis__beta_sync_tapping__istc_time_resolved.csv`
  - Time-resolved tapping coherence.
- `tables/analysis__beta_sync_tapping__istc_per_track.csv`
  - Per-track tapping coherence summary.
- `tables/analysis__beta_sync_tapping__kde_consensus_peaks.csv`
  - Human tapping consensus peak times.
- `tables/analysis__matlab_toolbox_features__mirtoolbox_binned_features.csv`
  - Time-binned MIRToolbox features.
- `tables/analysis__matlab_toolbox_features__miditoolbox_binned_features.csv`
  - Time-binned MIDI Toolbox features.

## Preliminary Results

- `tables/analysis__beta_sync_hypotheses__feature_coherence_correlations.csv`
  - Time-binned feature/coherence screen.
- `tables/analysis__beta_sync_hypotheses__whole_piece_mir_feature_correlations.csv`
  - Whole-piece MIR feature/coherence screens.
- `tables/analysis__beta_globaltap_canonical__optimizer_time_binned_within_track_correlations.csv`
  - Within-track time-binned relationships involving the exploratory optimizer outputs.
    Use rows where `target == istc_mean_max_unique_per_sec` for tapping
    concentration; `optimizer_*` target rows are optimizer quality-control screens.
- `docs/bach_100ms_feature_modeling_summary.md`
  - Short summary of the 100 ms correlation, regression, and Bayesian ridge screens.

## Code

The checked-in `tables/`, `audio_midi_t0/`, and `plots/` outputs are ready to
use directly. The `code/` folder contains the scripts used to generate them from
the full Bach workspace layout; some rebuild scripts expect source folders that
are not part of this collaborator package.
