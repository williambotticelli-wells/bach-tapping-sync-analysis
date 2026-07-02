# Bach 100 ms Feature Modeling Summary

These are screening analyses for MIDI/MIR/tapping feature relationships at 100 ms resolution. The within-track rows are the main local-effect screen; global correlations are included as context because they can reflect track-level differences.

## 100 ms Within-Track Signals

### tap_count_100ms
- `midi_active_note_count`: Spearman rho=0.038, q=2.99e-08, n=24816.
- `midi_note_onset_count_100ms`: Spearman rho=0.037, q=2.99e-08, n=24816.
- `midi_velocity_std`: Spearman rho=0.030, q=1.47e-05, n=24131.
- `midi_velocity_range`: Spearman rho=0.029, q=2.61e-05, n=24131.
- `midi_pitch_std`: Spearman rho=0.027, q=4.77e-05, n=24131.
- `midi_pitch_range`: Spearman rho=0.026, q=0.000119, n=24131.

## Bayesian Ridge Direction Screen

### tap_count_100ms
- `midi_pitch_mean`: beta=-0.046, P(direction)=0.959.
- `midi_pitch_std`: beta=0.051, P(direction)=0.938.
- `midi_active_note_count`: beta=0.009, P(direction)=0.740.
- `midi_velocity_std`: beta=0.017, P(direction)=0.715.
- `midi_velocity_mean`: beta=0.012, P(direction)=0.635.
- `midi_note_onset_count_100ms`: beta=0.001, P(direction)=0.577.

## Whole-Piece MIR/MIDI vs Track Coherence

### istc_mean_max_unique_per_sec
- `tap_count_mean_max_per_sec`: Spearman rho=0.997, q=2.5e-24, n=24.
- `max_tap_count_per_100ms_bin`: Spearman rho=0.798, q=0.000188, n=24.
- `max_unique_participants_per_100ms_bin`: Spearman rho=0.798, q=0.000188, n=24.
- `beta_perf`: Spearman rho=-0.575, q=0.159, n=24.
- `pitch_std`: Spearman rho=-0.528, q=0.31, n=24.

