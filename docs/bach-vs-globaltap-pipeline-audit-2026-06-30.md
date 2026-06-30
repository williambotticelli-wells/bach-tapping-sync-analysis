# Bach vs. GlobalTap / ISMIR Tapping Pipeline Audit — 2026-06-30

Reference: `/Users/ww577/Downloads/ISMIR_2026_GlobalTap_Submission (11).pdf`

## What The ISMIR / GlobalTap Pipeline Does

The GlobalTap paper describes the following analysis pipeline:

1. Collect REPP-aligned tap timings.
2. Pool taps across participants.
3. Compute KDE on a 5 ms grid with Gaussian bandwidth sigma = 80 ms.
4. Apply MAD outlier filtering around preliminary KDE peaks.
5. Extract KDE peaks with prominence >= 0.10 and minimum inter-peak distance of 150 ms.
6. Fit an optimized near-isochronous consensus beat grid.
7. Compute beat-sequence CV from the final optimized beat grid.
8. Compute ISTC as unique participants in sliding 100 ms bins, 50 ms step, max per 1 s, averaged over the listening window.
9. Compute split-half reliability/convergence of pooled tapping density.
10. Compare crowd beats to references or beat trackers using F-measure.
11. Render click-track overlays for perceptual validation.
12. Use CV and ISTC as intrinsic reliability predictors.

## What Has Been Run For Bach

The Bach beta-sync analysis currently includes:

- REPP-derived Bach tap parsing from usable trials.
- First-onset t=0 alignment using the beta-sync manifest.
- KDE consensus peaks using 80 ms bandwidth, 5 ms grid, 150 ms peak distance, and 0.10 prominence fraction.
- Trial-level mean IOI, perceived tempo, SD IOI, and trial CV IOI.
- Consensus peak IOIs and consensus beat-sequence CV from extracted KDE peaks.
- Canonical GlobalTap-style ISTC using unique participants in 100 ms bins / 50 ms step / 1 s max windows.
- Time-resolved ISTC on the same 1 s / 250 ms grid used for feature correlations.
- Participant-to-consensus IOI ratios.
- Python audio features, Python MIDI features, MATLAB MIRToolbox binned features, MIDI Toolbox binned and whole-piece features, and Nori/MIR whole-piece features.
- First-pass exploratory correlations between tapping concentration and binned audio/MIDI/MIR features.

Key driver:

- `scripts/build_bach_beta_analysis_tables.py`

Key outputs:

- `analysis/beta_sync_tapping/`
- `analysis/beta_sync_features/`
- `analysis/matlab_toolbox_features/`
- `analysis/beta_sync_multimodal/`
- `analysis/beta_sync_hypotheses/`

## What Is Not Yet Fully Ported From GlobalTap

The Bach pipeline does **not yet** include the full GlobalTap beat-grid/validation stack:

- MAD outlier filtering before final KDE recomputation is not explicitly included in the Bach consensus peak path.
- The optimized near-isochronous beat-grid stage from `companion_repo/optimization/run_pipeline.py` has not been run on Bach.
- Beat-sequence CV is currently computed from KDE consensus peaks, not from the fully optimized GlobalTap beat grid.
- Split-half density reliability and convergence/power curves have not yet been run specifically for Bach.
- F-measure against expert/reference beats or beat trackers has not yet been run for Bach.
- Click-track overlay validation stimuli have not yet been rendered for Bach crowd/MIDI/reference comparisons.
- Bimodal/tactus-level diagnostic classification has not yet been ported to Bach.

## Interpretation

The Bach tapping analyses are appropriate for exploratory feature/coherence work and for sharing synchronized time-resolved matrices with Rena. They are not yet a full Bach reproduction of the GlobalTap benchmark-building pipeline.

For Rena's immediate ECoG/audio-feature use case, the current tables are likely the right shareable format because they provide time-aligned features and tapping coherence on a common t=0 clock. For a paper-level claim that Bach crowd tapping yields consensus beat annotations comparable to GlobalTap, we should still run the missing grid-optimization, split-half, F-measure, and click-rendering steps.

## Recommended Next Analysis Tasks

1. Port GlobalTap's optimized beat-grid stage to Bach KDE peaks.
2. Recompute Bach beat-sequence CV from optimized grids.
3. Run Bach split-half reliability and convergence analyses.
4. If reference/MIDI beat grids are accepted as references, compute F-measure between Bach crowd consensus, MIDI-derived beat grids, and any algorithmic beat trackers.
5. Render Bach click-track overlays for crowd consensus vs MIDI/reference/algorithm beats.
6. Upgrade preliminary correlations to mixed/permutation models that respect repeated windows within tracks and repeated performances within WTC pieces.

