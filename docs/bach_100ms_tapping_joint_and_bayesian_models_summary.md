# Bach 100 ms Tapping: Joint Mixed-Effects and Hierarchical Bayesian Models

`run_bach_100ms_feature_models.py` and `run_bach_100ms_audio_feature_models.py`
screen local MIDI/acoustic features against `tap_count_100ms` one feature at a
time (within-track-centered correlation, then a closed-form multi-feature
Bayesian-ridge posterior). This doc covers two additions that bring the
tapping-only analysis up to the same standard applied to the emotion-slider
integration: a proper `statsmodels` mixed-effects regression with an explicit
per-track random effect, and a count-native hierarchical Bayesian model fit
with MCMC (PyMC/NUTS). Built to check whether the earlier univariate/ridge
screens were appropriately comprehensive, not to replace them -- both remain
useful as full per-feature sweeps.

## 1. Joint linear mixed-effects regression (`run_bach_tapping_mixed_regression.py`)

`tap_count_100ms ~ midi_active_note_count + midi_note_onset_count_100ms + midi_velocity_mean + midi_pitch_mean + audio100_rms + audio100_spectral_bandwidth_hz + audio100_spectral_centroid_hz`,
random intercept per `stim_name`, all variables z-scored, REML, n=24,131 bins
across 24 tracks.

| term | coef | se | p |
|---|---:|---:|---:|
| `midi_pitch_mean` | 0.017 | 0.007 | **0.013** |
| `audio100_spectral_bandwidth_hz` | -0.047 | 0.018 | **0.010** |
| `midi_velocity_mean` | -0.007 | 0.010 | 0.491 |
| `audio100_rms` | -0.004 | 0.010 | 0.700 |
| `midi_note_onset_count_100ms` | -0.004 | 0.008 | 0.630 |
| `midi_active_note_count` | -0.0004 | 0.008 | 0.966 |
| `audio100_spectral_centroid_hz` | -0.013 | 0.016 | 0.411 |
| track random-intercept variance | 0.061 | -- | -- |

**This is the headline finding of the joint model, and it changes the
interpretation of the univariate screens**: `midi_active_note_count` and
`midi_note_onset_count_100ms` are the *strongest* univariate within-track
correlates of tap concentration (Spearman rho highest of all MIDI features,
q<1e-7; see `bach_100ms_within_track_correlations.csv`), but both become
statistically indistinguishable from zero once fit jointly alongside pitch,
velocity, and spectral features. This is a collinearity effect: note density,
onset count, pitch range, and velocity range are all highly correlated
"textural density" proxies, and the univariate screen cannot tell them apart.
The joint model shows that, controlling for the others, it is specifically
**pitch height** (positive) and **spectral bandwidth** (negative) that carry
independent local information about tap concentration -- denser-but-narrower
spectral texture in a higher register goes with more tapping, not raw note
count per se. This is exactly the kind of confound the univariate screens
cannot resolve on their own, which is why this repo now runs both.

## 2. Hierarchical Bayesian model, count-native (`run_bach_tapping_hierarchical_bayesian_model.py`)

`tap_count_100ms` is an actual count (0 to several dozen tap events per
100 ms bin across ~10-13 online tappers), not a Likert-style aggregate, so
unlike the emotion-slider ratings it is modeled with its native likelihood
rather than a Gaussian approximation:

```
tap_count_100ms ~ NegativeBinomial(mu, alpha)
log(mu) = intercept + u_track[track] + beta . features_z
u_track ~ Normal(0, sigma_track)
```

Negative-binomial (rather than Poisson) because tap counts are visibly
overdispersed -- bursts around strong beats, near-zero elsewhere. A compact
4-feature model (same philosophy as the emotion ordinal model: a
well-specified check on the primary question, not a repeat of the full
per-feature sweep). Fit with NUTS, 4 chains x 2,000 draws (3,000 tune,
`target_accept=0.99`); **max r-hat = 1.008**, all ESS > 900 -- clean
convergence, on par with the emotion hierarchical models.

There is deliberately no participant-level random effect here (unlike the
emotion participant-trial model): this 100 ms table is already a crowd-level
aggregate count across all online tappers in a bin, and individual tapper
identifiers are not present at this resolution.

| term | posterior mean | sd | r-hat |
|---|---:|---:|---:|
| `midi_pitch_mean` | 0.017 | 0.006 | 1.00 |
| `midi_active_note_count` | -0.001 | 0.007 | 1.00 |
| `audio100_rms` | -0.015 | 0.009 | 1.00 |
| `audio100_spectral_bandwidth_hz` | **-0.071** | 0.010 | 1.00 |
| `sigma_track` (track random-intercept sd) | 0.276 | 0.044 | 1.01 |
| `alpha` (dispersion) | 2.186 | 0.046 | 1.00 |

Directionally identical to the MixedLM (pitch height positive, spectral
bandwidth negative and largest in magnitude, note count negligible once the
others are included) -- two independent estimation approaches (REML Gaussian
approximation vs. full Bayesian count model) agree. MCMC diagnostic (per-chain
posterior density + trace, confirming clean mixing/convergence):
`plots/bach_tapping_negbinom_hierarchical_bayesian_trace.png`. Plain-language
effect-size plot (posterior mean + 94% HDI per feature, this is the picture
that actually shows the result above):
`plots/bach_tapping_negbinom_hierarchical_bayesian_forest.png`.

## Why this was worth doing

The original 100 ms tapping screens (within-track correlation + closed-form
Bayesian ridge) were methodologically reasonable but answered a narrower
question ("which single features move together with tap concentration,
roughly controlling for collinearity via a ridge prior") than the mixed/
hierarchical treatment given to the emotion-slider data ("what is each
feature's independent effect, accounting for track as an explicit
random-effects grouping variable, with the outcome's actual likelihood").
Running the same tier of model here confirms the two headline univariate
"density" features were most likely proxies for pitch/spectral-texture
effects rather than independent local drivers -- a genuinely different (and
more defensible) conclusion than the univariate screen alone would suggest,
and the kind of correction that is easy to miss without a joint model.
