# Optimizer Feature Relationship Screens

These screens compare canonical GlobalTap optimizer outputs with MIRToolbox and MIDI Toolbox features at whole-piece and time-binned levels.

## Optimizer Path Summary

- Tracks analyzed: 24
- Bimodal route used: 13 tracks
- Balanced-lambda route used: 22 tracks
- Grid extension applied: 4 tracks

## Strongest Whole-Piece Screens

### bimodal_score
- `consensus_median_ioi_s`: Spearman rho=0.566, Pearson r=0.541, n=24.
- `consensus_tempo_bpm`: Spearman rho=-0.566, Pearson r=-0.509, n=24.
- `consensus_mean_ioi_s`: Spearman rho=0.540, Pearson r=0.514, n=24.
- `spectral_spread_Std`: Spearman rho=-0.534, Pearson r=-0.470, n=24.
- `spectral_rolloff95_Std`: Spearman rho=-0.500, Pearson r=-0.438, n=24.

### kde_curve_r_mean
- `unique_onset_count`: Spearman rho=0.434, Pearson r=0.498, n=24.
- `rhythm_attack_time_Mean`: Spearman rho=-0.426, Pearson r=-0.273, n=24.
- `n_notes`: Spearman rho=0.401, Pearson r=0.493, n=24.
- `spectral_centroid_Std`: Spearman rho=0.383, Pearson r=0.376, n=24.
- `spectral_spectentropy_Std`: Spearman rho=0.370, Pearson r=0.267, n=24.

### midi_onset_f_measure_diagnostic
- `consensus_mean_ioi_s`: Spearman rho=-0.663, Pearson r=-0.723, n=24.
- `Mel_subband_amplitude_std_27`: Spearman rho=0.662, Pearson r=0.434, n=24.
- `consensus_median_ioi_s`: Spearman rho=-0.662, Pearson r=-0.675, n=24.
- `consensus_tempo_bpm`: Spearman rho=0.662, Pearson r=0.659, n=24.
- `Mel_subband_amplitude_mean_28`: Spearman rho=0.650, Pearson r=0.455, n=24.

### optimized_beat_cv_ioi
- `rhythm_tempo_Mean`: Spearman rho=0.548, Pearson r=0.616, n=24.
- `pitch_max`: Spearman rho=0.512, Pearson r=0.569, n=24.
- `beat_sequence_cv_ioi`: Spearman rho=0.490, Pearson r=0.437, n=24.
- `beat_sequence_cv_ioi_pct`: Spearman rho=0.490, Pearson r=0.437, n=24.
- `spectral_mfcc_Mean_12`: Spearman rho=0.469, Pearson r=0.413, n=24.

### peak_f_mean
- `spectral_ddmfcc_Mean_8`: Spearman rho=-0.591, Pearson r=-0.516, n=24.
- `Mel_subband_amplitude_std_10`: Spearman rho=-0.488, Pearson r=-0.436, n=24.
- `Mel_subband_amplitude_mean_3`: Spearman rho=0.474, Pearson r=0.308, n=24.
- `spectral_mfcc_Mean_8`: Spearman rho=-0.473, Pearson r=-0.488, n=24.
- `spectral_mfcc_Mean_12`: Spearman rho=-0.467, Pearson r=-0.454, n=24.

### sample_size_for_kde_r_ge_0p9
- `spectral_mfcc_Mean_12`: Spearman rho=0.528, Pearson r=0.422, n=24.
- `spectral_mfcc_Mean_8`: Spearman rho=0.451, Pearson r=0.441, n=24.
- `spectral_rolloff85_Std`: Spearman rho=-0.420, Pearson r=-0.246, n=24.
- `n_participants_split`: Spearman rho=0.417, Pearson r=0.159, n=24.
- `n_trials`: Spearman rho=0.417, Pearson r=0.159, n=24.

### sample_size_for_peak_f_ge_0p8
- `spectral_ddmfcc_Mean_8`: Spearman rho=0.518, Pearson r=0.466, n=24.
- `Mel_subband_amplitude_std_10`: Spearman rho=0.448, Pearson r=0.362, n=24.
- `spectral_mfcc_Mean_12`: Spearman rho=0.442, Pearson r=0.294, n=24.
- `spectral_mfcc_Std_4`: Spearman rho=0.437, Pearson r=0.329, n=24.
- `spectral_dmfcc_Mean_11`: Spearman rho=-0.436, Pearson r=-0.427, n=24.

## Strongest Time-Binned Screens

### istc_mean_max_unique_per_sec
- `mtb_pitch_std`: Spearman rho=0.336, Pearson r=0.342, n=2874.
- `mtb_n_note_onsets`: Spearman rho=0.334, Pearson r=0.333, n=2880.
- `mtb_note_onset_density_per_s`: Spearman rho=0.334, Pearson r=0.333, n=2880.
- `n_note_onsets`: Spearman rho=0.333, Pearson r=0.332, n=2880.
- `note_onset_density_per_s`: Spearman rho=0.333, Pearson r=0.332, n=2880.

### max_tap_count_per_100ms_bin
- `mtb_pitch_std`: Spearman rho=0.345, Pearson r=0.350, n=2874.
- `mtb_n_note_onsets`: Spearman rho=0.343, Pearson r=0.341, n=2880.
- `mtb_note_onset_density_per_s`: Spearman rho=0.343, Pearson r=0.341, n=2880.
- `n_note_onsets`: Spearman rho=0.343, Pearson r=0.341, n=2880.
- `note_onset_density_per_s`: Spearman rho=0.343, Pearson r=0.341, n=2880.

### max_unique_participants_per_100ms_bin
- `mtb_pitch_std`: Spearman rho=0.345, Pearson r=0.351, n=2874.
- `mtb_n_note_onsets`: Spearman rho=0.342, Pearson r=0.341, n=2880.
- `mtb_note_onset_density_per_s`: Spearman rho=0.342, Pearson r=0.341, n=2880.
- `n_note_onsets`: Spearman rho=0.342, Pearson r=0.340, n=2880.
- `note_onset_density_per_s`: Spearman rho=0.342, Pearson r=0.340, n=2880.

### optimizer_beat_density_per_s
- `mtb_duration_mean_s`: Spearman rho=-0.280, Pearson r=-0.188, n=2874.
- `mean_note_duration_s`: Spearman rho=-0.280, Pearson r=-0.188, n=2874.
- `n_note_onsets`: Spearman rho=0.242, Pearson r=0.244, n=2880.
- `note_onset_density_per_s`: Spearman rho=0.242, Pearson r=0.244, n=2880.
- `mtb_n_note_onsets`: Spearman rho=0.241, Pearson r=0.244, n=2880.

### optimizer_peak_coverage_70ms
- `spectral_centroid_hz_std`: Spearman rho=0.117, Pearson r=0.058, n=2777.
- `mean_velocity`: Spearman rho=-0.111, Pearson r=-0.094, n=2771.
- `spectral_bandwidth_hz_std`: Spearman rho=0.093, Pearson r=0.039, n=2777.
- `spectral_rolloff_hz_std`: Spearman rho=0.093, Pearson r=0.043, n=2777.
- `mir_centroid`: Spearman rho=0.084, Pearson r=0.058, n=2777.

### optimizer_peak_density_per_s
- `n_note_onsets`: Spearman rho=0.134, Pearson r=0.138, n=2880.
- `note_onset_density_per_s`: Spearman rho=0.134, Pearson r=0.138, n=2880.
- `mtb_n_note_onsets`: Spearman rho=0.134, Pearson r=0.138, n=2880.
- `mtb_note_onset_density_per_s`: Spearman rho=0.134, Pearson r=0.138, n=2880.
- `mtb_active_note_count`: Spearman rho=0.133, Pearson r=0.149, n=2880.

### optimizer_peak_to_grid_median_abs_error_ms
- `mir_roughness`: Spearman rho=0.161, Pearson r=0.068, n=2777.
- `mean_velocity`: Spearman rho=0.155, Pearson r=0.096, n=2771.
- `onset_strength_mean`: Spearman rho=0.147, Pearson r=0.042, n=2777.
- `mtb_ioi_std_s`: Spearman rho=-0.142, Pearson r=-0.071, n=2710.
- `spectral_bandwidth_hz_std`: Spearman rho=-0.140, Pearson r=-0.032, n=2777.

## Strongest Within-Track Time-Binned Screens

### istc_mean_max_unique_per_sec
- `mtb_active_note_count`: within-track Spearman rho=0.274, Pearson r=0.353, n=2880.
- `active_note_count`: within-track Spearman rho=0.273, Pearson r=0.353, n=2880.
- `mtb_n_note_onsets`: within-track Spearman rho=0.250, Pearson r=0.306, n=2880.
- `mtb_note_onset_density_per_s`: within-track Spearman rho=0.250, Pearson r=0.306, n=2880.
- `n_note_onsets`: within-track Spearman rho=0.250, Pearson r=0.306, n=2880.

### max_tap_count_per_100ms_bin
- `mtb_active_note_count`: within-track Spearman rho=0.284, Pearson r=0.362, n=2880.
- `active_note_count`: within-track Spearman rho=0.283, Pearson r=0.362, n=2880.
- `mtb_n_note_onsets`: within-track Spearman rho=0.261, Pearson r=0.317, n=2880.
- `mtb_note_onset_density_per_s`: within-track Spearman rho=0.261, Pearson r=0.317, n=2880.
- `n_note_onsets`: within-track Spearman rho=0.261, Pearson r=0.316, n=2880.

### max_unique_participants_per_100ms_bin
- `mtb_active_note_count`: within-track Spearman rho=0.282, Pearson r=0.361, n=2880.
- `active_note_count`: within-track Spearman rho=0.282, Pearson r=0.361, n=2880.
- `mtb_n_note_onsets`: within-track Spearman rho=0.260, Pearson r=0.316, n=2880.
- `mtb_note_onset_density_per_s`: within-track Spearman rho=0.260, Pearson r=0.316, n=2880.
- `n_note_onsets`: within-track Spearman rho=0.260, Pearson r=0.316, n=2880.

### optimizer_beat_density_per_s
- `mean_pitch`: within-track Spearman rho=0.089, Pearson r=0.094, n=2874.
- `mtb_pitch_mean`: within-track Spearman rho=0.089, Pearson r=0.094, n=2874.
- `zero_crossing_rate_mean`: within-track Spearman rho=0.069, Pearson r=0.061, n=2880.
- `mean_velocity`: within-track Spearman rho=0.061, Pearson r=0.064, n=2874.
- `mir_brightness`: within-track Spearman rho=0.059, Pearson r=0.061, n=2880.

### optimizer_peak_coverage_70ms
- `mtb_ioi_mean_s`: within-track Spearman rho=-0.090, Pearson r=-0.094, n=2710.
- `mean_midi_ioi_s`: within-track Spearman rho=-0.090, Pearson r=-0.094, n=2710.
- `mtb_active_note_count`: within-track Spearman rho=0.071, Pearson r=0.109, n=2777.
- `mtb_pitch_std`: within-track Spearman rho=0.070, Pearson r=0.115, n=2771.
- `std_pitch`: within-track Spearman rho=0.069, Pearson r=0.115, n=2710.

### optimizer_peak_density_per_s
- `mtb_pitch_std`: within-track Spearman rho=0.115, Pearson r=0.111, n=2874.
- `rms_mean`: within-track Spearman rho=0.113, Pearson r=0.112, n=2880.
- `mir_rms`: within-track Spearman rho=0.112, Pearson r=0.110, n=2880.
- `std_pitch`: within-track Spearman rho=0.110, Pearson r=0.107, n=2809.
- `spectral_bandwidth_hz_mean`: within-track Spearman rho=-0.107, Pearson r=-0.123, n=2880.

### optimizer_peak_to_grid_median_abs_error_ms
- `mtb_ioi_mean_s`: within-track Spearman rho=0.104, Pearson r=0.109, n=2710.
- `mean_midi_ioi_s`: within-track Spearman rho=0.104, Pearson r=0.109, n=2710.
- `mtb_pitch_std`: within-track Spearman rho=-0.084, Pearson r=-0.120, n=2771.
- `std_pitch`: within-track Spearman rho=-0.080, Pearson r=-0.121, n=2710.
- `mtb_ioi_std_s`: within-track Spearman rho=-0.061, Pearson r=-0.034, n=2710.

## Interpretation Guardrails

- Time-binned rows overlap heavily, so p-values are screening diagnostics rather than inferential claims.
- MIDI-onset agreement remains an event/synchronization diagnostic, not a beat-reference benchmark.
- Participant-level data are not required for these screens; all outputs here are aggregate or feature-level.
