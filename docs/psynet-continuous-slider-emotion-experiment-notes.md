# PsyNet Continuous Slider Emotion Experiment Notes

Near-term goal: design a PsyNet experiment where participants listen to the same Bach pieces and continuously adjust a slider to indicate how strongly a target emotion is present moment-to-moment.

Starting points to inspect next:

- Harin's PsyNet implementation for push-button/time-event responses coupled to audio playback.
- PsyNet demos for synchronized audio playback plus continuous or repeated response collection.
- Existing Bach stimulus mapping from `beta_table.csv` and the beta-sync manifest, so emotion annotations can later join by `stim_name`, `wtc_code`, and time.

Design requirements:

- Audio playback and response timeline must share the same `t=0` convention used in the beta-sync Bach tables.
- Slider samples should be written with timestamps relative to stimulus onset, ideally at a fixed sampling interval or with event timestamps dense enough to bin later.
- Export should include participant ID, trial/stimulus ID, emotion prompt, slider value, timestamp, playback state, and any missed/paused/invalid sections.
- Output should be joinable to `analysis/beta_sync_multimodal/bach_time_binned_multimodal_with_matlab_toolboxes.csv` using the same bin grid or by later interpolation.

Open decisions:

- Whether each participant rates one emotion per trial or multiple emotions across repeated listens.
- Which emotion labels/scales to use first.
- Whether to collect continuous arousal/valence plus discrete emotions, or start with one discrete target.
- How much training/practice participants need to understand continuous rating.
