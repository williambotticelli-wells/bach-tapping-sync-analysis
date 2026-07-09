#!/usr/bin/env python3
"""Hierarchical Bayesian ordinal (ordered-logistic) mixed-effects models on
the raw 1-5 emotion-slider responses, at the participant-trial level
(n ~= 2400).

Why ordinal here specifically: the 100 ms and track-level tables use
`rating_mean`, an aggregate over ~20-50 raters/trials, which is a reasonable
continuous approximation by the CLT. At the participant-trial level we have
the raw discrete 1-5 response instead (approximated here by each trial's
mean rating rounded to the nearest integer -- a proxy for "overall impression
of the piece under that emotion lens"), where treating it as literally
continuous is more of a stretch. An ordered-logistic likelihood respects the
scale's actual ordinal structure (unequal psychological spacing between
categories) rather than assuming interval scaling.

Model (per emotion, fit separately -- the emotion x feature slopes are
allowed to differ, consistent with the sign-flips already seen in the
track-level and 100ms-bin-level per-emotion screens):

    rating_ordinal ~ OrderedLogistic(eta, cutpoints)
    eta = b_istc * istc_z + b_notedensity * notedensity_z + b_pitch * pitch_z
          + b_tempo * tempo_z + u_track[track] + u_participant[participant]
    u_track ~ Normal(0, sigma_track)
    u_participant ~ Normal(0, sigma_participant)

Fit with NUTS (PyMC). This is deliberately a compact, well-specified model
for the primary theoretical question (does tapping coherence and/or musical
feature structure predict how a piece is rated, beyond track/participant
random intercepts) -- not a repeat of the full exhaustive 100 ms sweep,
which would be computationally impractical (and largely redundant) as a full
MCMC hierarchical model per feature.

Outputs:
  - tables/analysis__beta_sync_emotion_models__bach_emotion_ordinal_bayesian_posterior_summary.csv
  - plots/bach_emotion_ordinal_bayesian_trace_<emotion>.png (MCMC diagnostic:
    per-chain posterior density + trace side by side, for the feature-effect
    and variance-component parameters. Uses arviz's `plot_trace_dist`, not
    `plot_trace` -- as of arviz>=1.0's plotting rewrite, `plot_trace` alone
    only draws the trace/mixing panel and silently drops the density panel,
    which makes the output look uninformative ("all noise") even though the
    underlying sampling is fine.)
  - plots/bach_emotion_ordinal_bayesian_forest_<emotion>.png (the
    substantive result: posterior mean + 94% HDI for each feature effect,
    i.e. what the trace plot's "beta" rows are actually estimating.)
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
TRIAL_LEVEL_PATH = REPO_ROOT / "tables" / "analysis__beta_sync_emotion__bach_participant_trial_level_table__redacted.csv"
OUT_SUMMARY = REPO_ROOT / "tables" / "analysis__beta_sync_emotion_models__bach_emotion_ordinal_bayesian_posterior_summary.csv"
PLOTS_DIR = REPO_ROOT / "plots"

EMOTIONS = ["happy", "sad", "calm", "energetic"]
FEATURES = [
    "istc_mean_max_unique_per_sec",
    "notedensity_per_s",
    "pitch_mean",
    "rhythm_tempo_Mean",
]
N_CATEGORIES = 5  # likert_5, categories 1..5 -> coded 0..4 for PyMC


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std(ddof=1)


def fit_one_emotion(df: pd.DataFrame, emotion: str, seed: int) -> tuple[pd.DataFrame, az.InferenceData]:
    sub = df[df["emotion_term"] == emotion].copy()
    sub = sub[sub["completed_audio"] == True]  # noqa: E712
    sub["rating_ordinal"] = sub["trial_mean_rating"].round().clip(1, 5).astype(int) - 1

    for f in FEATURES:
        sub[f + "_z"] = zscore(sub[f])

    track_idx, track_labels = pd.factorize(sub["stim_name"])
    participant_idx, participant_labels = pd.factorize(sub["participant_id"])
    n_tracks = len(track_labels)
    n_participants = len(participant_labels)

    coords = {
        "track": track_labels,
        "participant": participant_labels,
        "feature": FEATURES,
    }
    with pm.Model(coords=coords) as model:
        X = pm.Data("X", sub[[f + "_z" for f in FEATURES]].to_numpy())
        betas = pm.Normal("beta", mu=0.0, sigma=1.0, dims="feature")

        sigma_track = pm.HalfNormal("sigma_track", sigma=1.0)
        u_track_raw = pm.Normal("u_track_raw", mu=0.0, sigma=1.0, dims="track")
        u_track = pm.Deterministic("u_track", u_track_raw * sigma_track, dims="track")

        sigma_participant = pm.HalfNormal("sigma_participant", sigma=1.0)
        u_participant_raw = pm.Normal("u_participant_raw", mu=0.0, sigma=1.0, dims="participant")
        u_participant = pm.Deterministic(
            "u_participant", u_participant_raw * sigma_participant, dims="participant"
        )

        eta = pm.math.dot(X, betas) + u_track[track_idx] + u_participant[participant_idx]

        cutpoints = pm.Normal(
            "cutpoints",
            mu=np.arange(1, N_CATEGORIES) - (N_CATEGORIES) / 2.0,
            sigma=2.0,
            shape=N_CATEGORIES - 1,
            transform=pm.distributions.transforms.ordered,
            initval=np.arange(1, N_CATEGORIES) - (N_CATEGORIES) / 2.0,
        )

        pm.OrderedLogistic("rating", eta=eta, cutpoints=cutpoints, observed=sub["rating_ordinal"].to_numpy())

        idata = pm.sample(
            draws=1000,
            tune=1000,
            chains=4,
            cores=4,
            target_accept=0.95,
            random_seed=seed,
            progressbar=False,
        )

    summary = az.summary(idata, var_names=["beta", "sigma_track", "sigma_participant", "cutpoints"])
    summary = summary.reset_index().rename(columns={"index": "term"})
    summary.insert(0, "emotion_term", emotion)
    summary["n_obs"] = len(sub)
    summary["n_tracks"] = n_tracks
    summary["n_participants"] = n_participants
    rhat_ds = az.rhat(idata)
    summary["max_rhat"] = float(max(float(rhat_ds[v].max()) for v in rhat_ds.data_vars))
    return summary, idata


def main() -> None:
    PLOTS_DIR.mkdir(exist_ok=True)
    df = pd.read_csv(TRIAL_LEVEL_PATH, low_memory=False)

    all_summaries = []
    for i, emotion in enumerate(EMOTIONS):
        print(f"\n=== Fitting hierarchical ordinal-logistic model: {emotion} ===")
        summary, idata = fit_one_emotion(df, emotion, seed=20260704 + i)
        hdi_cols = [c for c in summary.columns if c.startswith("hdi_")]
        print(summary[["term", "mean", "sd"] + hdi_cols + ["r_hat"]].to_string(index=False))
        all_summaries.append(summary)

        az.plot_trace_dist(idata, var_names=["beta", "sigma_track", "sigma_participant"])
        plt.tight_layout()
        plt.savefig(PLOTS_DIR / f"bach_emotion_ordinal_bayesian_trace_{emotion}.png", dpi=100)
        plt.close("all")

        az.plot_forest(idata, var_names=["beta"], combined=True)
        plt.axvline(0, color="gray", linestyle="--", linewidth=1)
        plt.title(f"{emotion}: feature effects (posterior mean, 94% HDI)")
        plt.tight_layout()
        plt.savefig(PLOTS_DIR / f"bach_emotion_ordinal_bayesian_forest_{emotion}.png", dpi=100)
        plt.close("all")

    full_summary = pd.concat(all_summaries, ignore_index=True)
    full_summary.to_csv(OUT_SUMMARY, index=False)
    print(f"\nWrote {len(full_summary)} rows to {OUT_SUMMARY}")

    print("\n=== Beta (feature effect) posteriors, all emotions ===")
    hdi_cols = [c for c in full_summary.columns if c.startswith("hdi_")]
    betas_only = full_summary[full_summary["term"].str.startswith("beta[")]
    print(
        betas_only[["emotion_term", "term", "mean", "sd"] + hdi_cols + ["r_hat"]].to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
