# Bach 100 ms Emotion Feature Modeling Summary

Screening analyses relating 100 ms MIDI/acoustic/tap-count features to
aggregated emotion-slider ratings at the same 100 ms resolution, run
separately per emotion category. Within-track rows are the primary
local-effect screen (each track's own mean subtracted out); this
controls for track-level baseline differences in both the feature and
the rating, isolating local co-fluctuation.

`rating_mean` here is the mean over ~20-30 participants per bin, not a
raw individual response -- treated as continuous for this exhaustive
bin-level sweep (justified by aggregation over many raters per cell).
See the participant-trial-level hierarchical Bayesian ordinal models
for analysis of the raw 1-5 responses.

## 100 ms Within-Track Signals, By Emotion

### happy
- `midi_pitch_max`: Spearman rho=0.190, q=4.95e-193, n=24131.
- `midi_velocity_max`: Spearman rho=0.181, q=3.97e-175, n=24131.
- `midi_pitch_range`: Spearman rho=0.174, q=3e-162, n=24131.
- `midi_pitch_std`: Spearman rho=0.169, q=1.64e-152, n=24131.
- `audio100_spectral_bandwidth_hz`: Spearman rho=-0.162, q=1.06e-144, n=24816.
- `midi_velocity_mean`: Spearman rho=0.151, q=6.42e-122, n=24131.
- `audio100_rms`: Spearman rho=0.139, q=2.4e-106, n=24816.
- `midi_active_note_count`: Spearman rho=0.123, q=6.6e-84, n=24816.

### sad
- `midi_pitch_min`: Spearman rho=-0.138, q=3.62e-102, n=24131.
- `midi_pitch_range`: Spearman rho=0.131, q=6.92e-92, n=24131.
- `midi_pitch_std`: Spearman rho=0.111, q=2.15e-66, n=24131.
- `midi_velocity_range`: Spearman rho=0.076, q=8.62e-32, n=24131.
- `midi_active_note_count`: Spearman rho=0.076, q=4.52e-32, n=24816.
- `midi_pitch_mean`: Spearman rho=-0.073, q=2.96e-29, n=24131.
- `midi_velocity_max`: Spearman rho=0.062, q=3.03e-21, n=24131.
- `midi_velocity_std`: Spearman rho=0.051, q=3.46e-15, n=24131.

### calm
- `midi_velocity_min`: Spearman rho=-0.095, q=4.62e-48, n=24131.
- `audio100_rms`: Spearman rho=-0.080, q=5.8e-36, n=24816.
- `midi_velocity_mean`: Spearman rho=-0.069, q=2.58e-26, n=24131.
- `midi_velocity_range`: Spearman rho=0.063, q=5.39e-22, n=24131.
- `audio100_spectral_bandwidth_hz`: Spearman rho=0.062, q=6.09e-22, n=24816.
- `midi_pitch_range`: Spearman rho=0.060, q=4.18e-20, n=24131.
- `midi_velocity_std`: Spearman rho=0.048, q=3.48e-13, n=24131.
- `audio100_spectral_centroid_hz`: Spearman rho=0.046, q=1.63e-12, n=24816.

### energetic
- `audio100_spectral_bandwidth_hz`: Spearman rho=-0.279, q=0, n=24816.
- `midi_velocity_max`: Spearman rho=0.268, q=0, n=24131.
- `midi_velocity_mean`: Spearman rho=0.263, q=0, n=24131.
- `audio100_rms`: Spearman rho=0.257, q=0, n=24816.
- `midi_velocity_min`: Spearman rho=0.207, q=4.38e-231, n=24131.
- `midi_pitch_max`: Spearman rho=0.178, q=2.44e-171, n=24131.
- `midi_pitch_std`: Spearman rho=0.160, q=4.18e-138, n=24131.
- `midi_pitch_range`: Spearman rho=0.159, q=1.15e-135, n=24131.

## Bayesian Ridge Direction Screen, By Emotion

### happy
- `midi_pitch_std`: beta=0.241, P(direction)=1.000.
- `midi_velocity_mean`: beta=-0.181, P(direction)=1.000.
- `midi_velocity_std`: beta=-0.143, P(direction)=1.000.
- `audio100_spectral_bandwidth_hz`: beta=-0.142, P(direction)=1.000.
- `tap_count_100ms`: beta=0.122, P(direction)=1.000.
- `midi_active_note_count`: beta=0.085, P(direction)=1.000.
- `audio100_onset_strength_proxy`: beta=-0.050, P(direction)=1.000.
- `midi_note_onset_count_100ms`: beta=-0.028, P(direction)=1.000.

### sad
- `midi_pitch_std`: beta=0.268, P(direction)=1.000.
- `midi_velocity_std`: beta=-0.206, P(direction)=1.000.
- `midi_velocity_mean`: beta=-0.205, P(direction)=1.000.
- `midi_active_note_count`: beta=0.112, P(direction)=1.000.
- `audio100_spectral_rolloff_hz`: beta=0.094, P(direction)=1.000.
- `audio100_rms`: beta=0.088, P(direction)=1.000.
- `tap_count_100ms`: beta=0.072, P(direction)=1.000.
- `midi_note_onset_count_100ms`: beta=-0.050, P(direction)=1.000.

### calm
- `midi_pitch_std`: beta=0.284, P(direction)=1.000.
- `midi_active_note_count`: beta=0.168, P(direction)=1.000.
- `midi_velocity_std`: beta=-0.146, P(direction)=1.000.
- `tap_count_100ms`: beta=0.076, P(direction)=1.000.
- `midi_note_onset_count_100ms`: beta=-0.060, P(direction)=1.000.
- `audio100_spectral_rolloff_hz`: beta=0.062, P(direction)=1.000.
- `audio100_zero_crossing_rate`: beta=-0.030, P(direction)=0.998.
- `audio100_onset_strength_proxy`: beta=-0.021, P(direction)=0.996.

### energetic
- `audio100_spectral_bandwidth_hz`: beta=-0.223, P(direction)=1.000.
- `midi_pitch_std`: beta=0.159, P(direction)=1.000.
- `midi_velocity_mean`: beta=-0.141, P(direction)=1.000.
- `tap_count_100ms`: beta=0.133, P(direction)=1.000.
- `midi_active_note_count`: beta=0.066, P(direction)=1.000.
- `audio100_onset_strength_proxy`: beta=-0.055, P(direction)=1.000.
- `midi_pitch_mean`: beta=0.072, P(direction)=0.998.
- `audio100_spectral_rolloff_hz`: beta=0.044, P(direction)=0.998.

