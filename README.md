# Bach Tapping Sync + MIR/MIDI Analysis

This repository contains synchronized Bach audio/MIDI materials, tapping
coherence analyses, MIRToolbox/MIDI Toolbox features, preliminary
feature/coherence results, and continuous emotion-slider ratings (N=201
approved Prolific participants) joined onto the same stimulus set.

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
- Use `bach_emotion_slider_id_crosswalk.csv` and `docs/emotion_integration_summary.md` as the entry point for the emotion-slider data and how it joins onto everything above.
- Use `tables/analysis__beta_sync_tapping__raw_tap_events_per_trial__redacted.csv` and `tables/analysis__beta_sync_emotion__bach_raw_emotion_slider_samples.csv.gz` if you need the raw underlying data rather than the derived/aggregated tables above.

The checked-in tables and synchronized assets are ready to use directly. The
scripts in `code/` document how the package was built and can be rerun from the
full Bach workspace layout (see `requirements.txt` for the Python environment);
the GlobalTap optimizer script additionally expects the companion optimizer
repository next to the Bach workspace.

## Table Use

- 100 ms joins use `stim_name`, `wtc_code`, and `bin_center_s`.
- Time-binned joins use `stim_name`, `wtc_code`, and `window_center_s`.
- For local MIDI/tapping effects, start with the within-track screens. Global
  correlation tables are included as context and can reflect track-level
  differences.
- In optimizer tables, rows where `target == istc_mean_max_unique_per_sec`
  concern tapping concentration; rows with `optimizer_*` targets are optimizer
  quality-control screens.
- A few columns are exact duplicates of another column in the same table
  (e.g. `n_participants`/`n_trials`); see "Known Duplicate Columns" in
  `docs/data_guide.md` for the full list and which one to prefer.

## Most important tables

- `tables/bach_beta_midi_sync_manifest.csv`: canonical sync manifest.
- `tables/analysis__beta_sync_multimodal__bach_time_binned_multimodal_with_matlab_toolboxes.csv`: main time-binned analysis matrix.
- `tables/analysis__beta_sync_100ms__bach_100ms_midi_tapping_feature_vectors.csv`: 100 ms MIDI and tapping feature vectors for emotion/ECoG joins.
- `tables/analysis__beta_sync_100ms__bach_100ms_audio_feature_vectors.csv`: 100 ms acoustic feature vectors on the same grid.
- `tables/analysis__beta_sync_100ms__bach_100ms_audio_midi_tapping_feature_vectors.csv`: joined 100 ms acoustic/MIDI/tapping feature vectors.
- `tables/analysis__beta_sync_100ms_models__bach_100ms_audio_within_track_correlations.csv`: local 100 ms acoustic/tapping correlation screen.
- `tables/analysis__beta_sync_100ms_models__bach_100ms_within_track_correlations.csv`: local 100 ms MIDI/tapping correlation screen.
- `tables/analysis__beta_sync_100ms_models__bach_100ms_within_track_bayesian_ridge_screen.csv`: Bayesian ridge direction screen for the 100 ms MIDI/tapping vectors.
- `tables/analysis__beta_sync_100ms_models__bach_100ms_tapping_mixedlm_summary.csv`: joint mixed-effects regression (all MIDI/acoustic features + track random intercept) for local tap concentration.
- `tables/analysis__beta_sync_100ms_models__bach_tapping_negbinom_hierarchical_bayesian_posterior_summary.csv`: hierarchical Bayesian (negative-binomial, NUTS) model of the same question on the raw count outcome.
- `tables/analysis__matlab_toolbox_features__matlab_toolbox_feature_inventory.csv`: list of available feature sets.
- `tables/analysis__beta_sync_tapping__istc_per_track.csv`: per-track tapping coherence.
- `tables/analysis__beta_sync_tapping__istc_time_resolved.csv`: time-resolved tapping coherence.
- `tables/analysis__beta_sync_tapping__raw_tap_events_per_trial__redacted.csv`: raw per-trial tap-event timestamps (not a derived summary).
- `tables/analysis__beta_sync_hypotheses__feature_coherence_correlations.csv`: time-binned feature/coherence screen.
- `tables/analysis__beta_sync_hypotheses__whole_piece_mir_top_correlations.csv`: whole-piece MIR feature/coherence screens.
- `tables/analysis__beta_globaltap_canonical__bach_globaltap_style_track_summary.csv`: exploratory GlobalTap-style optimizer summary for Bach.
- `tables/analysis__beta_globaltap_canonical__split_half_reliability_first30s.csv`: first-30s split-half reliability.
- `tables/analysis__beta_globaltap_canonical__convergence_to_full_density_first30s.csv`: participant-count convergence screen.
- `tables/analysis__beta_globaltap_canonical__optimizer_whole_piece_feature_correlations.csv`: optimizer-stage metrics vs whole-piece MIR/MIDI features.
- `tables/analysis__beta_globaltap_canonical__optimizer_time_binned_within_track_correlations.csv`: local optimizer and tapping metrics vs time-binned MIR/MIDI features, centered within track.
- `tables/piece_mapping_notes.csv`: concise notes for tracks with piece-code corrections or mapping ambiguity.
- `bach_emotion_slider_id_crosswalk.csv`: stimulus-level crosswalk (slider `bach_XX` <-> `stim_name`/`trackN` <-> `manual_onset_s`) for the emotion-slider join.
- `tables/analysis__beta_sync_emotion__bach_100ms_full_multimodal_with_emotion.csv`: 100 ms acoustic/MIDI/tapping features joined with emotion ratings.
- `tables/analysis__beta_sync_emotion__bach_track_level_emotion_tapping_mir_midi_summary.csv`: song-wide emotion ratings joined with whole-piece MIR/MIDI/tapping features (n=96).
- `tables/analysis__beta_sync_emotion__bach_participant_trial_level_table__redacted.csv`: participant-trial-level ratings joined with track-level tapping/feature summaries (n=2,419).
- `tables/analysis__beta_sync_emotion__bach_raw_emotion_slider_samples.csv.gz`: raw, native-resolution (250 ms) slider samples underlying all of the above (n=1,021,641, gzip-compressed).
- `tables/analysis__beta_sync_emotion_models__bach_emotion_ordinal_bayesian_posterior_summary.csv`: hierarchical Bayesian ordered-logistic model posteriors for raw 1-5 ratings.

## Notes

- The source stimulus table contains 24 rows and 10 WTC piece codes.
- Participant-level trial tables are redacted by default: participant identifiers and source audio filenames are not included.
- The GlobalTap-style optimizer outputs are included as exploratory context and quality-control material.
- MIDI-onset agreement is a synchronization/event diagnostic, not true beat-tracker F1.
- ECoG data is not included in this repository. Emotion-slider data (N=201) is now included; see `docs/emotion_integration_summary.md`.
- The emotion-slider data comes from a separate study/participant pool than the tapping data -- they are linked only through the shared 24-stimulus set, not within-participant.
- Raw (not just derived/aggregated) data is included for both modalities: `analysis__beta_sync_tapping__raw_tap_events_per_trial__redacted.csv` (tap timestamps) and `analysis__beta_sync_emotion__bach_raw_emotion_slider_samples.csv.gz` (250 ms native slider samples). Both use this repo's existing redaction convention -- internal sequential/PsyNet ids only, no participant names, emails, Prolific/worker ids, or demographic fields.

## Preliminary signal

Across time bins, denser/active MIDI texture tends to coincide with higher tapping concentration, while broader/brighter spectral texture tends to coincide with lower tapping concentration. This should be treated as exploratory.

At the 100 ms MIDI/tapping resolution, the strongest within-track associations are positive but small: active-note count and MIDI onset count track local tap concentration. These vectors are best treated as alignment-ready inputs for emotion/ECoG models.

A joint mixed-effects model and a hierarchical Bayesian (negative-binomial) model of the same 100 ms tap-count outcome -- both with an explicit per-track random effect -- refine this: once note density, pitch, velocity, and spectral features are modeled together instead of one at a time, active-note count and onset count are no longer distinguishable from zero, while pitch height (positive) and spectral bandwidth (negative) remain credible independent predictors. See `docs/bach_100ms_tapping_joint_and_bayesian_models_summary.md`.

## Same-piece, between-performance comparisons

The 24 tracks are actually only **10 unique compositions** (8 performed twice, 2 performed 4 times -- not 12 pieces x 2, which was the nominal stimulus-list design before 2 slots turned out to be repeat performances; verified via raw MIDI pitch-sequence matching). Holding composition fixed this way, performance identity (tempo/dynamics/texture choices) explains 0-90%+ of variance depending on the outcome -- far more for tempo/dynamics/brightness than for tapping coherence or the emotion ratings, which are more piece- (composition-) dominated, especially `emotion_energetic` (93% piece-level). See `docs/bach_same_piece_performance_comparison_summary.md` for the ICC decomposition, the piece-random-intercept mixed models, and the n=8 paired-performance contrasts.

## Emotion-slider signal (preliminary; see `docs/emotion_integration_summary.md` for full detail)

Musical features predict emotion ratings robustly and in theoretically
coherent directions, both locally (100 ms, within-track: `energetic` rises
with velocity/RMS and falls with spectral bandwidth; `happy` rises with
pitch height) and song-wide (`energetic` vs. track duration/note density,
Spearman rho up to 0.93 in magnitude). A hierarchical Bayesian
ordered-logistic model on the raw 1-5 responses confirms credible,
opposite-signed note-density effects for `energetic`/`happy` vs.
`calm`/`sad`. By contrast, **tapping coherence itself shows no credible
relationship with emotion ratings at any level of analysis** (track-level
correlation, participant-trial mixed model, and the hierarchical Bayesian
model all agree) -- a consistent null, though the n=24-tracks structure of
the tapping data limits how small a true effect this design could detect.
