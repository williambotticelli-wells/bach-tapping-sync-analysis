# Analysis Summary

This repository contains synchronized Bach audio/MIDI materials, tapping
coherence analyses, and continuous emotion-slider ratings on the same
stimulus set. This doc covers the MIR/MIDI/tapping side specifically; see
`docs/emotion_integration_summary.md` for the emotion-slider integration and
`README.md` for the full table index.

## Core Timing Convention

All time-resolved tables use stimulus-relative time. `t=0` is the first musical
onset used in the synchronized audio/MIDI packet.

## Main Data Products

- Synchronized audio/MIDI files for 24 Bach stimuli.
- Per-track tapping coherence metrics: ISTC, KDE consensus peaks, IOI summaries,
  and participant-count convergence summaries.
- Time-binned MIRToolbox, MIDI Toolbox, audio, MIDI, and tapping-coherence
  features.
- Preliminary feature/coherence association tables.

## Preliminary Pattern

Across time bins, higher note activity and denser symbolic texture tend to align
with stronger tapping concentration. This is a screening result meant to guide
follow-up modeling with emotion and ECoG data.

The dedicated 100 ms MIDI/tapping vectors show the same direction but smaller
stand-alone effects: active-note count and MIDI onset count are positively
associated with local tap concentration after centering within track. The 100 ms
acoustic screen adds a matching audio feature grid: spectral bandwidth/centroid
are weakly negative with local tap count, while RMS is weakly positive. These
tables are also joined onto the emotion-slider ratings (see
`docs/emotion_integration_summary.md`).

A joint mixed-effects regression and a hierarchical Bayesian (negative-binomial)
model of the same 100 ms tap-count outcome -- fit with all features together
plus an explicit per-track random effect, rather than one feature at a time --
show that active-note count and onset count are not independently predictive
once pitch and spectral-bandwidth features are included; pitch height and
spectral bandwidth are the features that remain credible. See
`docs/bach_100ms_tapping_joint_and_bayesian_models_summary.md` for the full
comparison and why the univariate and joint results differ.

## Notes

- The source stimulus table contains 24 rows and 10 WTC piece codes.
- A small set of tracks has explicit piece-mapping notes in
  `tables/piece_mapping_notes.csv`.
- GlobalTap-style optimizer outputs are included as exploratory context and
  quality-control material. They are not required for the core MIR/MIDI/tapping/emotion joins.
- MIDI-onset agreement is a synchronization/event diagnostic, not a true
  beat-tracker F1 score.
