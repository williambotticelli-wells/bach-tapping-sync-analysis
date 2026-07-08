#!/usr/bin/env python3
"""Hierarchical Bayesian model for local (100 ms) tapping concentration,
count-native, with a random intercept per track.

This is the tapping-only counterpart to
`run_bach_emotion_hierarchical_bayesian_models.py`. `tap_count_100ms` is a
genuine count (number of tap events from ~10-13 online tappers in a 100 ms
bin, not a Likert rating), so unlike the emotion-slider ratings it is treated
with its native likelihood rather than an aggregate-then-Gaussian
approximation:

    tap_count_100ms ~ NegativeBinomial(mu, alpha)
    log(mu) = intercept + u_track[track] + beta . features_z
    u_track ~ Normal(0, sigma_track)

Negative-binomial (rather than Poisson) is used because tap counts across a
piece are noticeably overdispersed (bursts of dense tapping around strong
beats, near-zero counts elsewhere); a pure Poisson would understate
uncertainty. There is no participant-level random effect here because this
table is already a crowd-level aggregate (counts across all online tappers
per bin) -- individual participant identifiers are not present at this
resolution, unlike the participant-trial emotion table.

Fit with NUTS (PyMC), same 4-feature compact-model philosophy as the emotion
ordinal model (a well-specified check on the primary local-effect question,
not a repeat of the full per-feature sweep already in
`bach_100ms_within_track_bayesian_ridge_screen.csv`).

Outputs:
  - tables/analysis__beta_sync_100ms_models__bach_tapping_negbinom_hierarchical_bayesian_posterior_summary.csv
  - plots/bach_tapping_negbinom_hierarchical_bayesian_trace.png
"""

from __future__ import annotations

from pathlib import Path

import arviz as az
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymc as pm

REPO_ROOT = Path(__file__).resolve().parents[1]
IN_PATH = REPO_ROOT / "tables" / "analysis__beta_sync_100ms__bach_100ms_audio_midi_tapping_feature_vectors.csv"
OUT_SUMMARY = (
    REPO_ROOT
    / "tables"
    / "analysis__beta_sync_100ms_models__bach_tapping_negbinom_hierarchical_bayesian_posterior_summary.csv"
)
PLOTS_DIR = REPO_ROOT / "plots"

FEATURES = [
    "midi_active_note_count",
    "midi_pitch_mean",
    "audio100_rms",
    "audio100_spectral_bandwidth_hz",
]


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std(ddof=1)


def main() -> None:
    PLOTS_DIR.mkdir(exist_ok=True)
    df = pd.read_csv(IN_PATH, low_memory=False)
    cols = ["tap_count_100ms", "stim_name"] + FEATURES
    sub = df[cols].replace([np.inf, -np.inf], np.nan).dropna().copy()
    for f in FEATURES:
        sub[f + "_z"] = zscore(sub[f])

    track_idx, track_labels = pd.factorize(sub["stim_name"])
    n_tracks = len(track_labels)

    coords = {"track": track_labels, "feature": FEATURES}
    with pm.Model(coords=coords) as model:
        X = pm.Data("X", sub[[f + "_z" for f in FEATURES]].to_numpy())
        intercept = pm.Normal("intercept", mu=0.0, sigma=2.0)
        betas = pm.Normal("beta", mu=0.0, sigma=1.0, dims="feature")

        sigma_track = pm.HalfNormal("sigma_track", sigma=1.0)
        u_track_raw = pm.Normal("u_track_raw", mu=0.0, sigma=1.0, dims="track")
        u_track = pm.Deterministic("u_track", u_track_raw * sigma_track, dims="track")

        eta = intercept + pm.math.dot(X, betas) + u_track[track_idx]
        mu = pm.math.exp(eta)
        alpha = pm.HalfNormal("alpha", sigma=5.0)

        pm.NegativeBinomial("tap_count", mu=mu, alpha=alpha, observed=sub["tap_count_100ms"].to_numpy())

        idata = pm.sample(
            draws=2000,
            tune=3000,
            chains=4,
            cores=4,
            target_accept=0.99,
            random_seed=20260708,
            progressbar=False,
        )

    summary = az.summary(idata, var_names=["intercept", "beta", "sigma_track", "alpha"])
    summary = summary.reset_index().rename(columns={"index": "term"})
    summary["n_obs"] = len(sub)
    summary["n_tracks"] = n_tracks
    rhat_ds = az.rhat(idata)
    summary["max_rhat"] = float(max(float(rhat_ds[v].max()) for v in rhat_ds.data_vars))

    hdi_cols = [c for c in summary.columns if c.startswith("hdi_")]
    print(f"\n=== 100ms tapping NegBinomial hierarchical model (n={len(sub)}, tracks={n_tracks}) ===")
    print(summary[["term", "mean", "sd"] + hdi_cols + ["r_hat"]].to_string(index=False))

    summary.to_csv(OUT_SUMMARY, index=False)
    print(f"\nWrote {len(summary)} rows to {OUT_SUMMARY}")

    fig = az.plot_trace(idata, var_names=["intercept", "beta", "sigma_track", "alpha"])
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "bach_tapping_negbinom_hierarchical_bayesian_trace.png", dpi=100)
    plt.close("all")


if __name__ == "__main__":
    main()
