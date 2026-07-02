# Bach 100 ms Acoustic/MIR Feature Screen

- Feature source: `joined_100ms_audio_midi_tapping`.
- Features screened: 9.
- The within-track rows are the main local-effect screen; global rows are context.

## Top Within-Track Associations

- `audio100_spectral_bandwidth_hz`: Spearman rho=-0.036, q=1.51e-07, n=24816.
- `audio100_spectral_centroid_hz`: Spearman rho=-0.034, q=2.76e-07, n=24816.
- `audio100_rms`: Spearman rho=0.031, q=2.87e-06, n=24816.
- `mir100_centroid`: Spearman rho=-0.025, q=0.000156, n=24705.
- `mir100_brightness`: Spearman rho=-0.019, q=0.0042, n=24705.
- `mir100_roughness`: Spearman rho=0.019, q=0.0042, n=24792.
- `audio100_spectral_rolloff_hz`: Spearman rho=-0.017, q=0.0109, n=24816.
- `audio100_onset_strength_proxy`: Spearman rho=0.007, q=0.325, n=24816.

## Top Global Associations

- `audio100_spectral_bandwidth_hz`: Spearman rho=-0.048, q=6.22e-13, n=24816.
- `audio100_zero_crossing_rate`: Spearman rho=0.034, q=5.8e-07, n=24816.
- `audio100_onset_strength_proxy`: Spearman rho=0.032, q=1.34e-06, n=24816.
- `audio100_rms`: Spearman rho=0.020, q=0.00472, n=24816.
- `mir100_centroid`: Spearman rho=-0.013, q=0.0653, n=24705.
- `mir100_roughness`: Spearman rho=0.011, q=0.101, n=24792.
- `audio100_spectral_centroid_hz`: Spearman rho=-0.011, q=0.101, n=24816.
- `mir100_brightness`: Spearman rho=0.001, q=0.947, n=24705.
