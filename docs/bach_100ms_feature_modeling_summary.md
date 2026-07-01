# Bach 100 ms Feature Modeling Summary

These are screening analyses for MIDI/MIR/tapping feature relationships.

## 100 ms Within-Track Signals

### tap_count_100ms
- `midi_active_note_count`: Spearman rho=0.038, q=1.87e-08, n=24816.
- `midi_active_note_density_per_s`: Spearman rho=0.038, q=1.87e-08, n=24816.
- `midi_note_onset_count_100ms`: Spearman rho=0.037, q=1.87e-08, n=24816.
- `midi_note_onset_density_per_s`: Spearman rho=0.037, q=1.87e-08, n=24816.
- `midi_velocity_std`: Spearman rho=0.030, q=1.18e-05, n=24131.
- `midi_velocity_range`: Spearman rho=0.029, q=1.98e-05, n=24131.

### tap_density_per_s
- `midi_active_note_count`: Spearman rho=0.038, q=1.87e-08, n=24816.
- `midi_active_note_density_per_s`: Spearman rho=0.038, q=1.87e-08, n=24816.
- `midi_note_onset_count_100ms`: Spearman rho=0.037, q=1.87e-08, n=24816.
- `midi_note_onset_density_per_s`: Spearman rho=0.037, q=1.87e-08, n=24816.
- `midi_velocity_std`: Spearman rho=0.030, q=1.18e-05, n=24131.
- `midi_velocity_range`: Spearman rho=0.029, q=1.98e-05, n=24131.

### unique_tapper_count_100ms
- `midi_active_note_count`: Spearman rho=0.038, q=1.87e-08, n=24816.
- `midi_active_note_density_per_s`: Spearman rho=0.038, q=1.87e-08, n=24816.
- `midi_note_onset_count_100ms`: Spearman rho=0.037, q=1.87e-08, n=24816.
- `midi_note_onset_density_per_s`: Spearman rho=0.037, q=1.87e-08, n=24816.
- `midi_velocity_std`: Spearman rho=0.030, q=1.18e-05, n=24131.
- `midi_velocity_range`: Spearman rho=0.029, q=1.98e-05, n=24131.

## Bayesian Ridge Direction Screen

### tap_count_100ms
- `midi_pitch_mean`: beta=-0.046, P(direction)=0.957.
- `midi_pitch_std`: beta=0.051, P(direction)=0.938.
- `midi_velocity_std`: beta=0.017, P(direction)=0.709.
- `midi_velocity_mean`: beta=0.012, P(direction)=0.632.
- `midi_pitch_min`: beta=0.046, P(direction)=0.528.
- `midi_pitch_max`: beta=0.027, P(direction)=0.513.

### tap_density_per_s
- `midi_pitch_mean`: beta=-0.046, P(direction)=0.957.
- `midi_pitch_std`: beta=0.051, P(direction)=0.938.
- `midi_velocity_std`: beta=0.017, P(direction)=0.709.
- `midi_velocity_mean`: beta=0.012, P(direction)=0.632.
- `midi_pitch_min`: beta=0.046, P(direction)=0.528.
- `midi_pitch_max`: beta=0.027, P(direction)=0.513.

### unique_tapper_count_100ms
- `midi_pitch_mean`: beta=-0.047, P(direction)=0.959.
- `midi_pitch_std`: beta=0.050, P(direction)=0.934.
- `midi_velocity_std`: beta=0.018, P(direction)=0.718.
- `midi_velocity_mean`: beta=0.013, P(direction)=0.642.
- `midi_pitch_min`: beta=0.046, P(direction)=0.528.
- `midi_pitch_max`: beta=0.028, P(direction)=0.514.

## Whole-Piece MIR/MIDI vs Track Coherence

### istc_mean_max_unique_per_sec
- `beta_perf`: Spearman rho=-0.575, q=0.37, n=24.
- `pitch_std`: Spearman rho=-0.528, q=0.566, n=24.
- `unique_onset_count`: Spearman rho=0.445, q=0.702, n=24.
- `n_notes`: Spearman rho=0.410, q=0.844, n=24.
- `beta_score`: Spearman rho=-0.409, q=0.844, n=24.

### max_tap_count_per_100ms_bin
- `beta_perf`: Spearman rho=-0.643, q=0.267, n=24.
- `pitch_std`: Spearman rho=-0.591, q=0.366, n=24.
- `spectral_mfcc_Mean_13`: Spearman rho=-0.567, q=0.37, n=24.
- `beta_score`: Spearman rho=-0.522, q=0.566, n=24.
- `Mel_subband_amplitude_std_12`: Spearman rho=-0.508, q=0.62, n=24.

### max_unique_participants_per_100ms_bin
- `beta_perf`: Spearman rho=-0.643, q=0.267, n=24.
- `pitch_std`: Spearman rho=-0.591, q=0.366, n=24.
- `spectral_mfcc_Mean_13`: Spearman rho=-0.567, q=0.37, n=24.
- `beta_score`: Spearman rho=-0.522, q=0.566, n=24.
- `Mel_subband_amplitude_std_12`: Spearman rho=-0.508, q=0.62, n=24.

### tap_count_mean_max_per_sec
- `beta_perf`: Spearman rho=-0.599, q=0.366, n=24.
- `pitch_std`: Spearman rho=-0.524, q=0.566, n=24.
- `unique_onset_count`: Spearman rho=0.472, q=0.702, n=24.
- `n_notes`: Spearman rho=0.431, q=0.817, n=24.
- `beta_score`: Spearman rho=-0.430, q=0.817, n=24.

