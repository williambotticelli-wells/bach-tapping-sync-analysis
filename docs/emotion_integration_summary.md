# Emotion Slider Integration Summary

This documents how the continuous emotion-slider dataset (N=201 approved
Prolific participants, `happy`/`sad`/`calm`/`energetic`, 12 stimuli each, no
repeats) was joined onto the existing tapping/MIR/MIDI sync-analysis tables,
and summarizes the resulting correlational, mixed-effects regression, and
hierarchical Bayesian analyses. See `docs/data_guide.md` for the table index
and `docs/data_guide.md#emotion-tables` for column-level detail.

## Identifier crosswalk

`bach_emotion_slider_id_crosswalk.csv` (repo root) maps the slider's
`bach_01`..`bach_24` stimulus ids to this repo's `track1`..`track24` /
`stim_name` / `wtc_code`, and carries `manual_onset_s` for time alignment.
Built by `code/build_bach_emotion_id_crosswalk.py`, which:

- Joins on exact `oname` (deployed WAV basename) for 20 of 24 stimuli.
- Resolves the remaining 4 (`track8`/`track9`/`track10`/`track23`, all
  sharing filenames once the slider's own `" 2"`-suffix duplicate-audio fix
  is applied) via the same duration/onset cross-check already used
  independently by both this repo (`piece_mapping_notes.csv`) and the slider
  project's own audit (see `bach-project-audit-2026-06-30.md`,
  "Continuous Slider Experiment Audit", 2026-07-02 update) -- both
  cross-checks agree.
- Self-validates: asserts exactly 24 unique tracks/stimuli and a
  `manual_onset_s` for every one, and raises loudly if a future manifest edit
  breaks the mapping instead of silently mis-joining.

## Time alignment

The slider logs `time_s` as wall-clock-from-playback-start. Every other
time-resolved table in this repository uses `t=0` = first musical onset
(`manual_onset_s`, per track). We compute `t_sync = time_s - manual_onset_s`
before any binning; onset offsets range ~0.96-2.03 s across the 24 tracks
(`tables/bach_beta_midi_sync_manifest.csv`).

## Resampling to the 100 ms grid

The slider (`likert_5`, push-button) samples every 250 ms -- coarser than the
100 ms target grid -- and only changes value on a button press (a step
function). We assign each 100 ms bin the participant's most recently logged
value at or before that instant (`pandas.merge_asof`, `direction="backward"`,
grouped by participant x trial), rather than interpolating between presses,
since interpolation would invent ratings the participant never actually
displayed. `bin_center_s`/`bin_index` values are taken directly from
`analysis__beta_sync_100ms__bach_100ms_midi_tapping_feature_vectors.csv`
rather than re-derived, so they match exactly by construction.

**Known pre-existing float-precision quirk**: joins onto
`bach_100ms_audio_midi_tapping_feature_vectors.csv` must use `bin_index`
(int), not `bin_center_s` (float) -- that table and the MIDI/tapping table it
was combined from carry ~1e-16 to ~1e-9 floating-point drift on
`bin_center_s` for about 20 of 24,816 bins (pre-existing, not introduced by
this integration; harmless for a `bin_index` join, would silently drop ~19%
of rows on an exact-float join). All new join scripts here use `bin_index`.

## New tables (see `docs/data_guide.md` for full column lists)

| Table | Level | n |
|---|---|---|
| `bach_emotion_slider_id_crosswalk.csv` | stimulus | 24 |
| `analysis__beta_sync_emotion__bach_100ms_emotion_feature_vectors.csv` | 100 ms bin x emotion | 99,264 |
| `analysis__beta_sync_emotion__bach_100ms_full_multimodal_with_emotion.csv` | 100 ms bin x emotion, joined | 99,264 |
| `analysis__beta_sync_emotion__bach_track_level_emotion_tapping_mir_midi_summary.csv` | track x emotion (song-wide) | 96 |
| `analysis__beta_sync_emotion__bach_participant_trial_level_table__redacted.csv` | participant-trial | 2,419 |
| `analysis__beta_sync_emotion__bach_raw_emotion_slider_samples.csv.gz` | raw, per-sample (250 ms native) | 1,021,641 |

The last of these is the actual raw data everything else here aggregates or
bins -- see `docs/data_guide.md` for its exact provenance and
de-identification notes.

Model/screen outputs (`analysis__beta_sync_emotion_models__` prefix):
100 ms global + within-track correlations, within-track univariate
regressions, Bayesian-ridge screen, track-level correlations, MixedLM
summaries (bin- and trial-level), and the hierarchical Bayesian
ordered-logistic posterior summary.

## Statistical approach and why

- **100 ms bin level (n=99,264, ~20-30 raters/bin)**: `rating_mean` treated
  as continuous (CLT-justified at that aggregation level). Within-track
  centered Spearman/Pearson correlation with BH-FDR (mirrors this repo's
  existing `run_bach_100ms_feature_models.py` exactly, extended to the
  emotion targets: `run_bach_100ms_emotion_feature_models.py`), standardized
  univariate OLS, closed-form Bayesian-ridge direction screen, and a joint
  linear MixedLM (random intercept per track) per emotion.
- **Track level / song-wide (n=24, or n=96 pooled across emotions)**:
  Spearman correlation screen against ~185 whole-piece MIR/MIDI/tapping
  features per emotion. Small-n caveat applies exactly as it already does
  for this repo's own whole-piece MIR screens ("n=24 is too small for strong
  claims").
- **Participant-trial level (n=2,419, 206 participants)**: (a) a linear
  MixedLM with participant as the primary grouping factor and track as a
  variance component, testing whether track-level tapping coherence and
  whole-piece features predict trial ratings with individual-differences
  power; (b) a hierarchical **Bayesian ordered-logistic** model (PyMC, NUTS)
  on each trial's rating rounded to the nearest integer, with crossed
  Normal(0, sigma) random intercepts for track and participant -- this is
  the properly ordinal treatment of the raw 1-5 scale (the 100 ms and
  track-level continuous treatment is an aggregate-level approximation, not
  applied to raw individual responses).

## Headline findings (exploratory; see caveats above)

- **Musical feature -> rating**: robust, theoretically coherent local and
  song-wide effects. Locally (100 ms, within-track), `energetic` rises with
  MIDI velocity/RMS and falls with spectral bandwidth; `happy` rises with
  pitch height/range. Song-wide, `energetic` correlates strongly with faster
  tempo/higher note density (Spearman rho with `duration_mean_s` = -0.93;
  `calm`/`sad` show the mirror-image pattern). The hierarchical Bayesian
  model confirms credible, opposite-signed `notedensity_per_s` effects for
  `energetic`/`happy` (positive) vs. `calm`/`sad` (negative) with all
  99%-CI-equivalent HDIs excluding zero.
- **Local note/tap activity -> rating (all 4 emotions)**: in the joint
  100 ms MixedLM, both `midi_active_note_count` and `tap_count_100ms` load
  *positively* on every emotion's rating, not just `energetic` -- plausibly
  reflecting that denser passages draw more attention/engagement generally,
  intensifying whatever emotion is being rated, rather than a
  energetic-specific effect. Worth flagging to a domain expert before
  over-interpreting.
- **Tapping coherence -> rating (the main track<->emotion question)**: no
  credible relationship at any level. Track-level Spearman rho with
  `istc_mean_max_unique_per_sec` is small and non-significant for all 4
  emotions (|rho| <= 0.25, p >= 0.23, n=24). The participant-trial MixedLM
  gives coef=0.003 (p=0.895). The hierarchical Bayesian model's
  `istc_mean_max_unique_per_sec` posterior mean/sd ratio is <1.2 in
  magnitude for all 4 emotions (89-97% HDIs all include zero). This is a
  consistent null across 3 independent modeling approaches -- with the
  n=24-tracks caveat that this dataset cannot rule out a small true effect.
- **`sad` floor effect** (carried over from the earlier pilot audit):
  `sad` ratings remain compressed toward the low end
  (song-wide mean 2.01 vs. 2.51-3.04 for the other 3 emotions); still worth a
  scale/anchor review if `sad` is a primary outcome for future work.

## Caveats for downstream use

- Tapping and emotion are genuinely separate studies joined only by shared
  stimuli -- don't describe any result here as within-participant.
- `rating_mean` at 100 ms / track level is an aggregate; the participant-trial
  table + hierarchical Bayesian ordinal model is the only place raw 1-5
  responses are modeled as such.
- Several `sync_status` values in `bach_beta_midi_sync_manifest.csv` are
  still `midi_pending_confirmation` (this predates the emotion integration;
  see `bach-project-audit-2026-06-30.md`). MIDI-derived feature values for
  those tracks (not audio-derived ones) carry that pre-existing caveat.
- The 24-tracks/96-track-emotion-rows tables are small-n; treat any
  whole-piece correlation as a lead, not a confirmed effect.
