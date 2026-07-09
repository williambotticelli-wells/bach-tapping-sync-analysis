# Between-Performance Comparisons of the Same Piece

**Piece structure (verified, not assumed)**: the stimulus set was curated as 3 lists of 4 pieces x 2 performances (a nominal 12 piece-slots x 2 = 24), but 2 of those 12 slots turned out to be repeat performances of a piece already used in another list (`wtc1p03`, `wtc1p15`) rather than 2 new compositions -- confirmed by comparing raw MIDI pitch sequences across all 4 performances of each, which match closely. So there are **10 unique compositions**: 8 performed twice, 2 performed 4 times (8x2 + 2x4 = 24).

## 1. How much does performance (vs. composition) matter?

One-way random-effects ICC (unbalanced groups): fraction of total between-track variance attributable to *which piece* it is, vs. *which performance* of that piece it is.

| outcome | tracks | pieces | % variance: piece | % variance: performance |
|---|---:|---:|---:|---:|
| `istc_mean_max_unique_per_sec` | 24 | 10 | 43.5% | 56.5% |
| `emotion_happy` | 24 | 10 | 67.8% | 32.2% |
| `emotion_sad` | 24 | 10 | 73.8% | 26.2% |
| `emotion_calm` | 24 | 10 | 80.2% | 19.8% |
| `emotion_energetic` | 24 | 10 | 92.8% | 7.2% |
| `rhythm_tempo_Mean` | 24 | 10 | 61.3% | 38.7% |
| `notedensity_per_s` | 24 | 10 | 94.1% | 5.9% |
| `dynamics_rms_Mean` | 24 | 10 | 0.0% | 100.0% |
| `simple_brightness_Mean` | 24 | 10 | 41.9% | 58.1% |
| `pitch_mean` | 24 | 10 | 99.4% | 0.6% |
| `duration_mean_s` | 24 | 10 | 87.0% | 13.0% |

As expected, the acoustic/MIDI features that most directly encode *how a piece is composed* (pitch height, duration) are dominated by piece identity; tempo/dynamics/brightness -- the features most under a performer's control -- show a much larger performance-level share, confirming this decomposition is behaving sensibly before turning to the outcomes of actual interest (tapping coherence, emotion ratings). `dynamics_rms_Mean` shows 0%/100% because its raw (unclipped) ICC estimate was slightly negative -- within-piece performer-to-performer loudness variation is at least as large as piece-to-piece variation, i.e. how loud a *recording* is has essentially nothing to do with which piece it is, which is itself an informative (if not surprising) result.

## 2. Piece-random-intercept mixed regression (n=24 tracks, 10 pieces)

`outcome ~ tempo + note_density + dynamics + brightness + pitch + duration`, random intercept per piece (`wtc_code`), all variables z-scored. This asks: holding composition fixed via the random intercept, does a *specific performance's* tempo/dynamics/texture predict its tapping coherence or emotion ratings?

**Caveat up front**: n=24 tracks across only 10 piece-groups (most with only 2 members) gives this very little power to detect small effects or estimate the random-intercept variance precisely -- treat coefficients as directional leads, not confirmed effects.

### `istc_mean_max_unique_per_sec`
- `rhythm_tempo_Mean`: coef=0.090, p=0.746
- `notedensity_per_s`: coef=-1.495, p=0.022 **(p<0.05)**
- `dynamics_rms_Mean`: coef=0.502, p=0.038 **(p<0.05)**
- `simple_brightness_Mean`: coef=0.541, p=0.069
- `pitch_mean`: coef=0.085, p=0.717
- `duration_mean_s`: coef=-1.628, p=0.001 **(p<0.05)**
- `Group Var`: coef=0.000, p=1.000

### `emotion_happy`
- `rhythm_tempo_Mean`: coef=0.109, p=0.558
- `notedensity_per_s`: coef=-0.031, p=0.941
- `dynamics_rms_Mean`: coef=0.119, p=0.472
- `simple_brightness_Mean`: coef=0.591, p=0.008 **(p<0.05)**
- `pitch_mean`: coef=0.462, p=0.010 **(p<0.05)**
- `duration_mean_s`: coef=-0.659, p=0.036 **(p<0.05)**
- `Group Var`: coef=0.257, p=0.654

### `emotion_sad`
- `rhythm_tempo_Mean`: coef=-0.054, p=0.667
- `notedensity_per_s`: coef=-0.026, p=0.935
- `dynamics_rms_Mean`: coef=-0.243, p=0.054
- `simple_brightness_Mean`: coef=-0.401, p=0.017 **(p<0.05)**
- `pitch_mean`: coef=-0.126, p=0.447
- `duration_mean_s`: coef=0.926, p=0.001 **(p<0.05)**
- `Group Var`: coef=1.416, p=0.414

### `emotion_calm`
- `rhythm_tempo_Mean`: coef=0.086, p=0.560
- `notedensity_per_s`: coef=-0.873, p=0.006 **(p<0.05)**
- `dynamics_rms_Mean`: coef=-0.006, p=0.965
- `simple_brightness_Mean`: coef=-0.176, p=0.280
- `pitch_mean`: coef=0.007, p=0.960
- `duration_mean_s`: coef=0.108, p=0.650
- `Group Var`: coef=0.195, p=0.688

### `emotion_energetic`
- `rhythm_tempo_Mean`: coef=0.109, p=0.357
- `notedensity_per_s`: coef=0.474, p=0.143
- `dynamics_rms_Mean`: coef=0.033, p=0.795
- `simple_brightness_Mean`: coef=0.202, p=0.241
- `pitch_mean`: coef=0.195, p=0.297
- `duration_mean_s`: coef=-0.248, p=0.327
- `Group Var`: coef=1.818, p=0.259

## 3. Paired contrasts, 8 clean 2-performance pieces

Within each of the 8 pieces with exactly 2 performances, ordered faster-tempo performance minus slower-tempo performance, then correlated across the 8 pieces (delta-feature vs. delta-outcome). **n=8 -- treat as a lead, not a confirmed effect**; reported with exact Pearson/Spearman stats rather than significance stars for that reason.

Top |r| delta-delta associations:

| feature delta | outcome delta | n | Pearson r | p | Spearman rho | p |
|---|---|---:|---:|---:|---:|---:|
| `notedensity_per_s` | `emotion_calm` | 8 | -0.525 | 0.181 | -0.476 | 0.233 |
| `duration_mean_s` | `emotion_calm` | 8 | 0.349 | 0.397 | 0.381 | 0.352 |
| `pitch_mean` | `emotion_calm` | 8 | -0.301 | 0.469 | -0.214 | 0.610 |
| `dynamics_rms_Mean` | `emotion_calm` | 8 | -0.213 | 0.612 | -0.048 | 0.911 |
| `simple_brightness_Mean` | `emotion_calm` | 8 | 0.158 | 0.708 | -0.095 | 0.823 |
| `rhythm_tempo_Mean` | `emotion_calm` | 8 | 0.121 | 0.776 | 0.500 | 0.207 |
| `pitch_mean` | `emotion_energetic` | 8 | 0.563 | 0.146 | -0.095 | 0.823 |
| `notedensity_per_s` | `emotion_energetic` | 8 | 0.528 | 0.179 | 0.643 | 0.086 |
| `dynamics_rms_Mean` | `emotion_energetic` | 8 | 0.495 | 0.213 | 0.381 | 0.352 |
| `simple_brightness_Mean` | `emotion_energetic` | 8 | -0.488 | 0.220 | -0.310 | 0.456 |

## 4. The two 4-performance pieces (descriptive supplement)

Not pooled into the n=8 paired analysis above (a 4-performance piece contributes 6 non-independent pairs, not 1); reported as within-piece spread (SD, range, CV) instead.

| piece | column | n perf | mean | sd | range | CV |
|---|---|---:|---:|---:|---:|---:|
| wtc1p03 | `istc_mean_max_unique_per_sec` | 4 | 6.712 | 0.496 | 1.126 | 0.074 |
| wtc1p03 | `rhythm_tempo_Mean` | 4 | 129.128 | 0.747 | 1.569 | 0.006 |
| wtc1p03 | `emotion_happy` | 4 | 3.281 | 0.099 | 0.210 | 0.030 |
| wtc1p03 | `emotion_sad` | 4 | 1.634 | 0.221 | 0.488 | 0.136 |
| wtc1p03 | `emotion_calm` | 4 | 2.109 | 0.217 | 0.469 | 0.103 |
| wtc1p03 | `emotion_energetic` | 4 | 3.627 | 0.215 | 0.484 | 0.059 |
| wtc1p15 | `istc_mean_max_unique_per_sec` | 4 | 5.920 | 0.478 | 1.039 | 0.081 |
| wtc1p15 | `rhythm_tempo_Mean` | 4 | 145.909 | 10.408 | 23.300 | 0.071 |
| wtc1p15 | `emotion_happy` | 4 | 3.174 | 0.376 | 0.764 | 0.118 |
| wtc1p15 | `emotion_sad` | 4 | 1.548 | 0.114 | 0.265 | 0.074 |
| wtc1p15 | `emotion_calm` | 4 | 1.796 | 0.269 | 0.634 | 0.150 |
| wtc1p15 | `emotion_energetic` | 4 | 3.781 | 0.209 | 0.459 | 0.055 |

