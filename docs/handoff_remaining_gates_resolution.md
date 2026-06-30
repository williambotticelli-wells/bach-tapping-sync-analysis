# Bach Handoff Remaining-Gates Resolution

## Corpus Mapping

- `beta_table.csv` rows: 24
- WTC codes in `beta_table.csv`: 10
- WTC codes represented in current manifest: 10
- WTC codes missing from current manifest: 0
- Tracks where beta-table piece label disagrees with final manifest `wtc_code`: 4
- Specific mapping-confirmation tracks: track10, track23, track8, track9
- The current handoff should describe the manifest as 24 deployed tracks from the beta table, not as a clean 12-piece x 2-performance set, until Rena/Nori confirms the intended grouping.

## Optimizer Click QC

- Click-preview rows prepared: 24
- High-priority rows for manual listening: 24
- Use `optimizer_click_qc_manifest.csv` to mark whether the canonical optimizer clicks sound aligned to the perceptual beat and whether any track needs exclusion or manual annotation.

## Inferential Screens

- FDR-corrected versions of the main correlation screens were written to this folder.
- A piece-level meta screen was added for within-track time-binned optimizer-feature correlations.
- These are still screening analyses because windows overlap and the corpus mapping needs final confirmation.

## Beat-Tracker F1

- Local Bach beat/reference/tracker candidate files found: 22
- No true beat-reference table for these Bach stimuli was identified locally. Current MIDI-onset F-measure should remain labeled as an event/synchronization diagnostic.
- To compute real F1, add beat-reference or algorithm beat CSVs on the same `t=0` timebase, then compare `optimized_crowd_beats_first30s.csv` against those references with a beat-tolerance window.

## Data Gates

- ECoG and emotion-rating joins remain blocked until those datasets exist on the same `t=0` clock.
- The current Rena packet is appropriate for sync review, feature/coherence review, and deciding which tracks are reliable enough for neural/emotion modeling.
