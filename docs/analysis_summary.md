# Analysis Summary

This repository contains synchronized Bach audio/MIDI materials and exploratory
tapping-analysis outputs for use with emotion-rating and ECoG analyses.

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
associated with local tap concentration after centering within track. These
tables are most useful as high-resolution inputs for later emotion/ECoG joins.
The 100 ms screens use aggregate tapping and MIDI features suitable for later
emotion/ECoG joins.

## Notes

- The source stimulus table contains 24 rows and 10 WTC piece codes.
- A small set of tracks has explicit piece-mapping notes in
  `tables/piece_mapping_notes.csv`.
- GlobalTap-style optimizer outputs are included as exploratory context and
  quality-control material. They are not required for the core emotion/ECoG join.
- MIDI-onset agreement is a synchronization/event diagnostic, not a true
  beat-tracker F1 score.
