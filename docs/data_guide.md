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
- `tables/analysis__beta_sync_100ms__bach_100ms_audio_feature_vectors.csv`
  - 100 ms acoustic feature-vector table on the same grid. It includes RMS,
    zero-crossing rate, spectral centroid/bandwidth/rolloff, and an onset-strength
    proxy. Join on `stim_name`, `wtc_code`, and `bin_center_s`.
- `tables/analysis__beta_sync_100ms__bach_100ms_audio_midi_tapping_feature_vectors.csv`
  - Joined 100 ms acoustic/MIDI/tapping table. Use this when a single table is
    more convenient than joining the separate vectors.
- `tables/analysis__beta_sync_100ms_models__bach_100ms_within_track_correlations.csv`
  - Within-track 100 ms correlation screen relating local MIDI features to local
    tap concentration.
- `tables/analysis__beta_sync_100ms_models__bach_100ms_audio_within_track_correlations.csv`
  - Within-track 100 ms correlation screen relating local acoustic features to
    local tap concentration.
- `tables/analysis__beta_sync_100ms_models__bach_100ms_within_track_bayesian_ridge_screen.csv`
  - Bayesian ridge direction screen using the same 100 ms feature vectors.
- `tables/analysis__beta_sync_100ms_models__bach_100ms_tapping_mixedlm_summary.csv`
  - Joint linear mixed-effects regression (all MIDI/acoustic features together,
    random intercept per track) for local tap concentration -- see
    `docs/bach_100ms_tapping_joint_and_bayesian_models_summary.md`.
- `tables/analysis__beta_sync_100ms_models__bach_tapping_negbinom_hierarchical_bayesian_posterior_summary.csv`
  - Hierarchical Bayesian (negative-binomial, track random intercept, NUTS)
    model of the same question, fit on the raw count outcome; see the same doc.
- `tables/analysis__beta_sync_tapping__istc_time_resolved.csv`
  - Time-resolved tapping coherence.
- `tables/analysis__beta_sync_tapping__istc_per_track.csv`
  - Per-track tapping coherence summary.
- `tables/analysis__beta_sync_tapping__kde_consensus_peaks.csv`
  - Human tapping consensus peak times.
- `tables/analysis__beta_sync_tapping__raw_tap_events_per_trial__redacted.csv`
  - Raw tap-event timestamps per trial (one row per trial, `taps_s` is a
    JSON-encoded list of tap times on the `t=0`-at-first-onset clock). The
    only tapping table that is not a derived summary. `trial_row` matches
    `trial_ioi_metrics__redacted.csv` / `ioi_ratio_per_trial__redacted.csv`
    exactly (same redaction convention: no `participant_uid`/`audio_filename`).
    Built by `code/build_bach_raw_tap_events_export.py` (requires the full
    Bach workspace layout to rebuild; the checked-in CSV does not).
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
- `docs/bach_100ms_audio_feature_modeling_summary.md`
  - Short summary of the 100 ms acoustic/MIR-style feature screen.
- `docs/bach_100ms_tapping_joint_and_bayesian_models_summary.md`
  - Joint mixed-effects and hierarchical Bayesian follow-up on the above two
    screens: local tap-count effects that look independent in the univariate
    screens turn out to be collinear "density" proxies once modeled jointly.

## Same-Piece Performance-Comparison Tables

There are only **10 unique compositions** among the 24 tracks, not 12 (2 of
the stimulus set's nominal 12 "list slots" turned out to be repeat
performances of a piece used elsewhere rather than new compositions --
verified by comparing raw MIDI pitch sequences). 8 compositions have exactly
2 performances; 2 (`wtc1p03`, `wtc1p15`) have 4. See
`docs/bach_same_piece_performance_comparison_summary.md` for the full
verification and results.

- `tables/analysis__beta_sync_performance_pairs__bach_same_piece_performance_long.csv`
  - One row per track: whole-piece MIR/MIDI features, tapping coherence, and
    each emotion's track-level mean rating, plus `n_performances_this_piece`.
- `tables/analysis__beta_sync_performance_pairs__bach_same_piece_icc_variance_decomposition.csv`
  - What fraction of total between-track variance in each outcome is
    between-piece (composition) vs. within-piece-between-performance.
- `tables/analysis__beta_sync_performance_pairs__bach_same_piece_mixedlm_summary.csv`
  - Piece-random-intercept mixed regression (n=24, 10 pieces): do a specific
    performance's tempo/dynamics/texture predict its coherence/ratings,
    controlling for which piece it is.
- `tables/analysis__beta_sync_performance_pairs__bach_same_piece_paired_contrasts.csv` / `..._paired_delta_correlations.csv`
  - The 8 clean 2-performance pieces only: within-pair deltas (faster-tempo
    performance minus slower) and their cross-piece correlations.
- `tables/analysis__beta_sync_performance_pairs__bach_four_performance_pieces_supplement.csv`
  - Descriptive within-piece spread for the 2 four-performance pieces
    (kept separate from the n=8 paired analysis to avoid double-counting
    non-independent pairs).

## Emotion Tables

Continuous emotion-slider data (N=201 approved Prolific participants,
`happy`/`sad`/`calm`/`energetic`, 1 locked emotion/participant, 12 of 24
stimuli each). See `docs/emotion_integration_summary.md` for the full join
methodology, time-alignment/resampling details, and headline findings; this
section is the column-level index.

- `bach_emotion_slider_id_crosswalk.csv` (repo root)
  - Stimulus-level crosswalk: `stimulus_id` (slider `bach_XX`) <->
    `stim_name` (`trackN`) <-> `wtc_code` <-> `manual_onset_s`. Built by
    `code/build_bach_emotion_id_crosswalk.py`.
- `tables/analysis__beta_sync_emotion__bach_100ms_emotion_feature_vectors.csv`
  - 100 ms emotion rating vectors, aggregated across participants. One row
    per `(stim_name, emotion_term, bin_index)`. Join on `stim_name`,
    `wtc_code`, and **`bin_index`** (not `bin_center_s` -- see float-drift
    note below). Columns: `rating_mean`, `rating_sd`, `rating_se`,
    `n_ratings`, `n_participants`.
- `tables/analysis__beta_sync_emotion__bach_100ms_full_multimodal_with_emotion.csv`
  - The above joined onto `bach_100ms_audio_midi_tapping_feature_vectors.csv`.
    Long format on `emotion_term` (MIDI/audio/tap columns repeat across each
    track's up-to-4 emotion rows per bin, since those don't depend on
    emotion). Use this when you want features + emotion in one table.
- `tables/analysis__beta_sync_emotion__bach_track_level_emotion_tapping_mir_midi_summary.csv`
  - Song-wide: one row per `(stim_name, emotion_term)`, n=96. Rating is the
    across-participant mean of each participant's own per-trial mean rating.
    Joined onto the existing whole-piece MIR/MIDI + `istc_per_track`
    columns (all 204 columns from
    `bach_track_level_mir_midi_coherence_table.csv` are carried over).
- `tables/analysis__beta_sync_emotion__bach_participant_trial_level_table__redacted.csv`
  - Participant-trial level, n=2,419 (206 participants). One row per
    participant x trial: rating summary stats, trial metadata (duration,
    familiarity, enjoyment, difficulty, trial order), emotion_term, and a
    compact set of the track's tapping/whole-piece features (not all 204 --
    see the script for the exact list). `participant_id` is the
    already-anonymized PsyNet-internal id (export used `--anonymize both`),
    consistent with this repo's redacted-participant-table convention.
- `tables/analysis__beta_sync_emotion__bach_raw_emotion_slider_samples.csv.gz`
  - Raw, native-resolution (250 ms) slider samples: one row per
    (participant, trial, sample), n=1,021,641, gzip-compressed (~14 MB). This
    is the actual data every other emotion table in this repo aggregates or
    bins -- use it if you need a different bin width than 100 ms, or want to
    inspect individual response trajectories. Adds `stim_name`, `wtc_code`,
    and `t_sync` (`= time_s - manual_onset_s`, the same aligned clock used
    everywhere else) via the crosswalk; all other columns are exactly what
    the PsyNet export produced. `participant_id` is the same anonymized
    PsyNet-internal id as above (same underlying `--anonymize both` export);
    no demographic, geographic, or free-text fields are present. Built by
    `code/export_bach_raw_emotion_slider_samples.py` (needs the
    non-shipped `scratch/emotion_source_data/` flat export to rebuild).
- `tables/analysis__beta_sync_emotion_models__*`
  - Correlation/regression/Bayesian screens and summaries built from the
    tables above; see `docs/emotion_integration_summary.md` for what each
    one answers and the headline results.

**Float-precision note (pre-existing, not introduced by the emotion
integration)**: `bach_100ms_midi_tapping_feature_vectors.csv` and
`bach_100ms_audio_midi_tapping_feature_vectors.csv` carry ~1e-16 to ~1e-9
floating-point drift on `bin_center_s` for ~20 of 24,816 bins. Join 100 ms
tables on `bin_index` (exact int), not `bin_center_s`, to avoid silently
dropping ~19% of rows on an exact-float join.

## Known Duplicate Columns

A handful of columns are exact numeric duplicates of another column in the same
table. They are kept (rather than silently dropped) because they come from a
genuinely different source file, but you only need to read one of each pair:

- `n_participants` / `n_trials`: identical in this dataset because every
  participant contributes exactly one trial per track. Prefer `n_participants`.
- `max_tap_count_per_100ms_bin` / `max_unique_participants_per_100ms_bin`
  (track-level coherence table only): identical because no participant taps
  twice in the same 100 ms bin. Prefer `max_unique_participants_per_100ms_bin`.

Several other duplicate-by-construction columns were removed outright rather
than kept: `mir100_rms` (bit-identical to `audio100_rms` — RMS on a fixed
100 ms window has no algorithm-specific choices, so the Python and MATLAB
pipelines agree exactly), `mtb_note_onset_density_per_s` (an exact rescaling of
`mtb_n_note_onsets` by the fixed window size), `optimizer_peak_count`/
`optimizer_beat_count` (the optimizer time-binned windows are always exactly
1 s, so the `_density_per_s` columns are identical and are kept instead), and
`cv_ioi_pct` (a literal duplicate of `trial_cv_ioi_pct` in the per-trial IOI
tables). The chroma-strength columns were also dropped from the time-binned
multimodal table because they require `librosa`, which was unavailable when
these tables were built, and were 100% missing.

## Code

The checked-in `tables/`, `audio_midi_t0/`, and `plots/` outputs are ready to
use directly. The `code/` folder contains the scripts used to generate them from
the full Bach workspace layout; some rebuild scripts expect source folders that
are not part of this collaborator package.

`code/bach_run_100ms_mirtoolbox_features.m` provides a MATLAB/MIRToolbox route
for short-window RMS, brightness, roughness, and centroid features.
`code/build_bach_100ms_audio_features.py` is the dependency-light Python route
used for the checked-in 100 ms acoustic vectors. `code/join_bach_100ms_audio_midi_tapping_features.py`
builds the joined 100 ms acoustic/MIDI/tapping table.
