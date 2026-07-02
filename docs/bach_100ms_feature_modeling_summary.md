# Bach 100 ms Feature Modeling Summary

These are screening analyses for MIDI/MIR/tapping feature relationships. Redundant fixed-bin rescalings are omitted: `tap_count_100ms` is the single 100 ms tapping-concentration target, and count/range predictors are used instead of exact density/dynamic-range duplicates.

## 100 ms Within-Track Signal

### tap_count_100ms
- `midi_active_note_count`: Spearman rho=0.038, q=1.87e-08, n=24816.
- `midi_note_onset_count_100ms`: Spearman rho=0.037, q=1.87e-08, n=24816.
- `midi_velocity_std`: Spearman rho=0.030, q=1.18e-05, n=24131.
- `midi_velocity_range`: Spearman rho=0.029, q=1.98e-05, n=24131.
- `midi_pitch_std`: Spearman rho=0.027, q=3.73e-05, n=24131.
- `midi_pitch_range`: Spearman rho=0.026, q=9.95e-05, n=24131.

## Bayesian Ridge Direction Screen

### tap_count_100ms
- `midi_pitch_mean`: beta=-0.046, P(direction)=0.957.
- `midi_pitch_std`: beta=0.051, P(direction)=0.938.
- `midi_velocity_std`: beta=0.017, P(direction)=0.709.
- `midi_velocity_mean`: beta=0.012, P(direction)=0.632.
- `midi_pitch_min`: beta=0.046, P(direction)=0.528.
- `midi_pitch_max`: beta=0.027, P(direction)=0.513.

## Whole-Piece MIR/MIDI vs Track Coherence

### istc_mean_max_unique_per_sec
- `beta_perf`: Spearman rho=-0.575, q=0.37, n=24.
- `pitch_std`: Spearman rho=-0.528, q=0.566, n=24.
- `unique_onset_count`: Spearman rho=0.445, q=0.702, n=24.
- `n_notes`: Spearman rho=0.410, q=0.844, n=24.
- `beta_score`: Spearman rho=-0.409, q=0.844, n=24.

## Caveat

- These rows remain exploratory screens; p-values are not confirmatory because time bins are nested within tracks and adjacent bins are not independent.
