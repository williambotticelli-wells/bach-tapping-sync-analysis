# Candidate Bach GlobalTap-Style Findings

These are screening results from the first 30 s of each Bach stimulus, matching the GlobalTap excerpt window more closely than the full-piece exploratory tables.

## Reliability Signal

- Median split-half KDE correlation: 0.582.
- Median split-half peak F-measure: 0.555.
- Most reliable tracks: track7, track8, track2, track9, track14, track3, track20, track16.
- Weakest reliability tracks: track6, track12, track1, track4, track5, track21, track11, track22.

## Convergence Signal

- Median participant count to reach KDE r >= .90 against the full crowd: 11.0.
- Fastest convergence: track8, track9, track7, track16, track3.
- Slowest convergence: track21, track10, track17, track19, track12.

## Top Feature Screens

### kde_curve_r_mean
- `sample_size_for_peak_f_ge_0p8`: Spearman rho=-0.679, Pearson r=-0.761, n=24.
- `bimodal_score`: Spearman rho=-0.527, Pearson r=-0.388, n=24.
- `unique_onset_count`: Spearman rho=0.434, Pearson r=0.498, n=24.
- `rhythm_attack_time_Mean`: Spearman rho=-0.426, Pearson r=-0.273, n=24.
- `n_notes`: Spearman rho=0.401, Pearson r=0.493, n=24.

### midi_onset_f_measure_diagnostic
- `optimized_median_ioi_s`: Spearman rho=-0.691, Pearson r=-0.724, n=24.
- `consensus_mean_ioi_s`: Spearman rho=-0.663, Pearson r=-0.723, n=24.
- `Mel_subband_amplitude_std_27`: Spearman rho=0.662, Pearson r=0.434, n=24.
- `consensus_median_ioi_s`: Spearman rho=-0.662, Pearson r=-0.675, n=24.
- `consensus_tempo_bpm`: Spearman rho=0.662, Pearson r=0.659, n=24.

### optimized_tempo_bpm
- `optimized_median_ioi_s`: Spearman rho=-1.000, Pearson r=-0.978, n=24.
- `n_optimized_beats`: Spearman rho=0.993, Pearson r=0.996, n=24.
- `consensus_median_ioi_s`: Spearman rho=-0.883, Pearson r=-0.861, n=24.
- `consensus_tempo_bpm`: Spearman rho=0.883, Pearson r=0.870, n=24.
- `consensus_mean_ioi_s`: Spearman rho=-0.839, Pearson r=-0.871, n=24.

### peak_f_mean
- `sample_size_for_peak_f_ge_0p8`: Spearman rho=-0.906, Pearson r=-0.885, n=24.
- `spectral_ddmfcc_Mean_8`: Spearman rho=-0.591, Pearson r=-0.516, n=24.
- `tap_retention_after_mad`: Spearman rho=-0.536, Pearson r=-0.464, n=24.
- `Mel_subband_amplitude_std_10`: Spearman rho=-0.488, Pearson r=-0.436, n=24.
- `optimized_beat_cv_ioi`: Spearman rho=-0.480, Pearson r=-0.430, n=24.

### sample_size_for_kde_r_ge_0p9
- `sample_size_for_peak_f_ge_0p8`: Spearman rho=0.906, Pearson r=0.854, n=24.
- `spectral_mfcc_Mean_12`: Spearman rho=0.528, Pearson r=0.422, n=24.
- `spectral_mfcc_Mean_8`: Spearman rho=0.451, Pearson r=0.441, n=24.
- `spectral_rolloff85_Std`: Spearman rho=-0.420, Pearson r=-0.246, n=24.
- `n_participants`: Spearman rho=0.417, Pearson r=0.159, n=24.

## Same-Piece/Performance Notes

- Unique WTC codes in this manifest: 10.
- WTC codes with exactly two performances: 8.
- `same_piece_globaltap_style_summary.csv` lists each piece's two-performance grouping and reliability/tempo spread.

## Caveats

- The optimized grid here uses the companion-repo GlobalTap optimizer cascade.
- MIDI-onset F-measure is an event/synchronization diagnostic, not a ground-truth beat-tracker benchmark.
- The strongest shareable result remains the tapping reliability/convergence pattern plus its relationship to MIR/MIDI feature screens; emotion and ECoG joins remain future data gates.
