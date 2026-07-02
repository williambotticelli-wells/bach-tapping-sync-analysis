# Bach 100 ms Acoustic/MIR Feature Screen

- Feature source: `joined_100ms_audio_midi_tapping`.
- Features screened: 10.
- The within-track rows are the main local-effect screen; global rows are context.

## Top Within-Track Associations

- `audio100_spectral_bandwidth_hz`: Spearman rho=-0.036, q=1.68e-07, n=24816.
- `audio100_spectral_centroid_hz`: Spearman rho=-0.034, q=3.07e-07, n=24816.
- `audio100_rms`: Spearman rho=0.031, q=3.19e-06, n=24816.
- `mir100_rms`: Spearman rho=0.030, q=7.27e-06, n=24792.
- `mir100_centroid`: Spearman rho=-0.025, q=0.000138, n=24705.
- `mir100_brightness`: Spearman rho=-0.019, q=0.004, n=24705.
- `mir100_roughness`: Spearman rho=0.019, q=0.004, n=24792.
- `audio100_spectral_rolloff_hz`: Spearman rho=-0.017, q=0.0106, n=24816.

## Top Global Associations

- `audio100_spectral_bandwidth_hz`: Spearman rho=-0.048, q=6.91e-13, n=24816.
- `audio100_zero_crossing_rate`: Spearman rho=0.034, q=6.45e-07, n=24816.
- `audio100_onset_strength_proxy`: Spearman rho=0.032, q=1.49e-06, n=24816.
- `audio100_rms`: Spearman rho=0.020, q=0.00524, n=24816.
- `mir100_rms`: Spearman rho=0.018, q=0.00776, n=24792.
- `mir100_centroid`: Spearman rho=-0.013, q=0.0605, n=24705.
- `mir100_roughness`: Spearman rho=0.011, q=0.0982, n=24792.
- `audio100_spectral_centroid_hz`: Spearman rho=-0.011, q=0.0982, n=24816.
