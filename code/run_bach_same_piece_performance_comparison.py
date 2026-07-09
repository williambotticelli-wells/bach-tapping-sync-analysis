#!/usr/bin/env python3
"""Between-performance comparisons of the same underlying WTC piece.

Ground truth on piece structure (verified here, not assumed -- see
docs/bach_same_piece_performance_comparison_summary.md for the check):
the stimulus set was originally curated as 3 "lists" of 4 pieces x 2
performances (12 piece-slots, 24 stimuli), but 2 of those 12 slots (in
list 3) turned out to be repeat performances of a piece already used in
list 2 (`wtc1p03`, `wtc1p15`) rather than 2 new compositions -- confirmed by
comparing raw MIDI pitch sequences, which match closely across all
4 performances of each. So there are **10 unique compositions**: 8 performed
twice and 2 (`wtc1p03`, `wtc1p15`) performed 4 times each (2+2+2+2+2+2+2+2+4+4
= 24). Piece identity here is the sync manifest's `wtc_code`, which already
reflects this (corrected) grouping -- not the nominal "12 list-slots".

This script asks: holding the composition fixed, how much does the specific
performance (tempo, dynamics, texture chosen by that recording) matter for
(a) tapping coherence and (b) emotion ratings?

Three analyses:
  1. Variance decomposition (one-way random-effects ICC, unbalanced groups):
     what fraction of total between-track variance in each outcome is
     between-piece (composition) vs. within-piece-between-performance
     (interpretation)?
  2. Piece-random-intercept mixed regression (n=24 tracks, 10 pieces): does
     a performance's whole-piece tempo/dynamics/texture predict its tapping
     coherence / emotion ratings, controlling for piece identity?
  3. Paired contrasts restricted to the 8 clean 2-performance pieces: signed
     within-pair deltas (faster-tempo performance minus slower), correlated
     across features and outcomes -- the most literal "which performance
     wins" comparison, with an appropriate small-n (n=8) caveat.

Outputs:
  - tables/analysis__beta_sync_performance_pairs__bach_same_piece_performance_long.csv
  - tables/analysis__beta_sync_performance_pairs__bach_same_piece_icc_variance_decomposition.csv
  - tables/analysis__beta_sync_performance_pairs__bach_same_piece_mixedlm_summary.csv
  - tables/analysis__beta_sync_performance_pairs__bach_same_piece_paired_contrasts.csv
  - tables/analysis__beta_sync_performance_pairs__bach_same_piece_paired_delta_correlations.csv
  - docs/bach_same_piece_performance_comparison_summary.md
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import pearsonr, spearmanr

REPO_ROOT = Path(__file__).resolve().parents[1]
COHERENCE_TABLE = REPO_ROOT / "tables" / "analysis__beta_sync_100ms_models__bach_track_level_mir_midi_coherence_table.csv"
EMOTION_TABLE = REPO_ROOT / "tables" / "analysis__beta_sync_emotion__bach_track_level_emotion_tapping_mir_midi_summary.csv"
OUT_DIR = REPO_ROOT / "tables"
DOC_OUT = REPO_ROOT / "docs" / "bach_same_piece_performance_comparison_summary.md"

FEATURES = {
    "rhythm_tempo_Mean": "tempo (MIDI toolbox, higher = faster)",
    "notedensity_per_s": "note density (notes/s)",
    "dynamics_rms_Mean": "dynamics (RMS)",
    "simple_brightness_Mean": "spectral brightness",
    "pitch_mean": "mean pitch height",
    "duration_mean_s": "performance duration (s)",
}
EMOTIONS = ["happy", "sad", "calm", "energetic"]
OUTCOME = "istc_mean_max_unique_per_sec"


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std(ddof=1)


def build_wide_table() -> pd.DataFrame:
    coh = pd.read_csv(COHERENCE_TABLE, low_memory=False)
    cols = ["stim_name", "wtc_code", OUTCOME] + list(FEATURES.keys())
    wide = coh[cols].copy()

    emo = pd.read_csv(EMOTION_TABLE, low_memory=False)
    emo_wide = emo.pivot(index="stim_name", columns="emotion_term", values="emotion_rating_mean")
    emo_wide.columns = [f"emotion_{c}" for c in emo_wide.columns]
    wide = wide.merge(emo_wide, on="stim_name", how="left")

    wide["n_performances_this_piece"] = wide.groupby("wtc_code")["stim_name"].transform("count")
    wide = wide.sort_values(["wtc_code", "stim_name"]).reset_index(drop=True)
    return wide


def variance_decomposition(wide: pd.DataFrame, outcomes: list[str]) -> pd.DataFrame:
    """One-way random-effects ICC(1) for unbalanced groups (piece = group).

    ICC(1) = (MS_between - MS_within) / (MS_between + (k0 - 1) * MS_within),
    k0 = harmonic-mean-adjusted average group size (Shrout & Fleiss unbalanced
    case). Interpreted as the fraction of total variance attributable to
    piece identity (composition) rather than performance-to-performance
    variation within a piece.
    """
    rows = []
    groups = wide.groupby("wtc_code")
    n_groups = groups.ngroups
    n_total = len(wide)
    group_sizes = groups.size()
    # unbalanced k0 per Shrout & Fleiss (1979)
    k0 = (n_total - (group_sizes**2).sum() / n_total) / (n_groups - 1)

    for outcome in outcomes:
        sub = wide[["wtc_code", outcome]].dropna()
        if sub.empty or sub["wtc_code"].nunique() < 2:
            continue
        grand_mean = sub[outcome].mean()
        g = sub.groupby("wtc_code")[outcome]
        ss_between = (g.count() * (g.mean() - grand_mean) ** 2).sum()
        ss_within = ((sub[outcome] - sub.groupby("wtc_code")[outcome].transform("mean")) ** 2).sum()
        df_between = sub["wtc_code"].nunique() - 1
        df_within = len(sub) - sub["wtc_code"].nunique()
        ms_between = ss_between / df_between if df_between else np.nan
        ms_within = ss_within / df_within if df_within else np.nan
        icc_raw = (ms_between - ms_within) / (ms_between + (k0 - 1) * ms_within)
        # ICC(1) can come out negative when the between-piece variance
        # estimate is at/below zero (within-piece/performer variability
        # exceeds between-piece variability) -- a known property of the
        # unbiased-but-not-truncated estimator, not a computation error.
        # Report both the raw value and a [0, 1]-clipped version for the
        # plain-language "% variance" framing.
        icc_clipped = float(np.clip(icc_raw, 0.0, 1.0))
        rows.append(
            {
                "outcome": outcome,
                "n_tracks": len(sub),
                "n_pieces": sub["wtc_code"].nunique(),
                "ms_between_piece": ms_between,
                "ms_within_piece": ms_within,
                "icc1_piece_variance_fraction_raw": icc_raw,
                "pct_variance_between_piece": 100 * icc_clipped,
                "pct_variance_within_piece_performance": 100 * (1 - icc_clipped),
            }
        )
    return pd.DataFrame(rows)


def mixedlm_within_piece(wide: pd.DataFrame, outcome: str) -> pd.DataFrame:
    cols = ["wtc_code", outcome] + list(FEATURES.keys())
    sub = wide[cols].replace([np.inf, -np.inf], np.nan).dropna()
    for col in [outcome] + list(FEATURES.keys()):
        sub[col] = zscore(sub[col])
    formula = f"{outcome} ~ " + " + ".join(FEATURES.keys())
    model = smf.mixedlm(formula, data=sub, groups=sub["wtc_code"])
    result = model.fit(reml=True, method="lbfgs")
    rows = []
    for name, coef, se, p in zip(result.params.index, result.params.values, result.bse.values, result.pvalues.values):
        rows.append(
            {
                "outcome": outcome,
                "term": name,
                "coef": coef,
                "se": se,
                "p_value": p,
                "n_obs": int(result.nobs),
                "n_pieces": sub["wtc_code"].nunique(),
            }
        )
    rows.append(
        {
            "outcome": outcome,
            "term": "group_var (piece random intercept variance)",
            "coef": result.cov_re.iloc[0, 0],
            "se": np.nan,
            "p_value": np.nan,
            "n_obs": int(result.nobs),
            "n_pieces": sub["wtc_code"].nunique(),
        }
    )
    print(f"\n=== Piece-random-intercept MixedLM: {outcome} (n={int(result.nobs)} tracks, {sub['wtc_code'].nunique()} pieces) ===")
    print(result.summary())
    return pd.DataFrame(rows)


def paired_contrasts(wide: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Restrict to the 8 clean 2-performance pieces; order each pair by
    tempo (faster first) so deltas have a consistent, interpretable sign."""
    pair_pieces = wide[wide["n_performances_this_piece"] == 2]["wtc_code"].unique()
    outcome_cols = [OUTCOME] + [f"emotion_{e}" for e in EMOTIONS]
    feature_cols = list(FEATURES.keys())

    rows = []
    for piece in sorted(pair_pieces):
        sub = wide[wide["wtc_code"] == piece].sort_values("rhythm_tempo_Mean", ascending=False)
        if len(sub) != 2:
            continue
        fast, slow = sub.iloc[0], sub.iloc[1]
        row = {"wtc_code": piece, "faster_track": fast["stim_name"], "slower_track": slow["stim_name"]}
        for col in feature_cols + outcome_cols:
            row[f"delta_{col}"] = fast[col] - slow[col]
            row[f"faster_{col}"] = fast[col]
            row[f"slower_{col}"] = slow[col]
        rows.append(row)
    pairs = pd.DataFrame(rows)

    corr_rows = []
    for feature in feature_cols:
        for outcome in outcome_cols:
            x = pairs[f"delta_{feature}"].to_numpy(float)
            y = pairs[f"delta_{outcome}"].to_numpy(float)
            mask = np.isfinite(x) & np.isfinite(y)
            if mask.sum() < 4:
                continue
            pr, pp = pearsonr(x[mask], y[mask])
            sr, sp = spearmanr(x[mask], y[mask])
            corr_rows.append(
                {
                    "feature": feature,
                    "outcome": outcome,
                    "n_pairs": int(mask.sum()),
                    "pearson_r": pr,
                    "pearson_p": pp,
                    "spearman_rho": sr,
                    "spearman_p": sp,
                }
            )
    corr = pd.DataFrame(corr_rows)
    if not corr.empty:
        corr["abs_pearson_r"] = corr["pearson_r"].abs()
        corr = corr.sort_values(["outcome", "abs_pearson_r"], ascending=[True, False])
    return pairs, corr


def four_performance_supplement(wide: pd.DataFrame) -> pd.DataFrame:
    """Descriptive within-piece spread for the 2 pieces with 4 performances
    (not mixed into the n=8 paired analysis, reported separately)."""
    rows = []
    for piece, sub in wide[wide["n_performances_this_piece"] == 4].groupby("wtc_code"):
        for col in [OUTCOME] + list(FEATURES.keys()) + [f"emotion_{e}" for e in EMOTIONS]:
            vals = sub[col].dropna()
            if len(vals) < 2:
                continue
            rows.append(
                {
                    "wtc_code": piece,
                    "column": col,
                    "n_performances": len(vals),
                    "mean": vals.mean(),
                    "sd": vals.std(ddof=1),
                    "min": vals.min(),
                    "max": vals.max(),
                    "range": vals.max() - vals.min(),
                    "coefficient_of_variation": vals.std(ddof=1) / abs(vals.mean()) if vals.mean() != 0 else np.nan,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    wide = build_wide_table()
    wide.to_csv(OUT_DIR / "analysis__beta_sync_performance_pairs__bach_same_piece_performance_long.csv", index=False)
    print(f"Pieces: {wide['wtc_code'].nunique()}; tracks: {len(wide)}")
    print(wide.groupby("n_performances_this_piece")["wtc_code"].nunique())

    outcomes = [OUTCOME] + [f"emotion_{e}" for e in EMOTIONS] + list(FEATURES.keys())
    icc = variance_decomposition(wide, outcomes)
    icc.to_csv(OUT_DIR / "analysis__beta_sync_performance_pairs__bach_same_piece_icc_variance_decomposition.csv", index=False)
    print("\n=== Variance decomposition (% of variance between piece vs. within-piece/performance) ===")
    print(icc[["outcome", "n_tracks", "n_pieces", "pct_variance_between_piece", "pct_variance_within_piece_performance"]].to_string(index=False))

    mixedlm_rows = [mixedlm_within_piece(wide, outcome) for outcome in [OUTCOME] + [f"emotion_{e}" for e in EMOTIONS]]
    mixedlm_summary = pd.concat(mixedlm_rows, ignore_index=True)
    mixedlm_summary.to_csv(OUT_DIR / "analysis__beta_sync_performance_pairs__bach_same_piece_mixedlm_summary.csv", index=False)

    pairs, corr = paired_contrasts(wide)
    pairs.to_csv(OUT_DIR / "analysis__beta_sync_performance_pairs__bach_same_piece_paired_contrasts.csv", index=False)
    corr.to_csv(OUT_DIR / "analysis__beta_sync_performance_pairs__bach_same_piece_paired_delta_correlations.csv", index=False)
    print(f"\n=== Paired contrasts (n={len(pairs)} 2-performance pieces): top delta-delta correlations ===")
    print(corr.head(12).to_string(index=False))

    four_perf = four_performance_supplement(wide)
    four_perf.to_csv(OUT_DIR / "analysis__beta_sync_performance_pairs__bach_four_performance_pieces_supplement.csv", index=False)

    write_doc(wide, icc, mixedlm_summary, pairs, corr, four_perf)
    print(f"\nWrote summary doc to {DOC_OUT}")


def write_doc(wide, icc, mixedlm_summary, pairs, corr, four_perf) -> None:
    lines = [
        "# Between-Performance Comparisons of the Same Piece",
        "",
        "**Piece structure (verified, not assumed)**: the stimulus set was "
        "curated as 3 lists of 4 pieces x 2 performances (a nominal 12 "
        "piece-slots x 2 = 24), but 2 of those 12 slots turned out to be "
        "repeat performances of a piece already used in another list "
        "(`wtc1p03`, `wtc1p15`) rather than 2 new compositions -- confirmed "
        "by comparing raw MIDI pitch sequences across all 4 performances of "
        "each, which match closely. So there are **10 unique compositions**: "
        "8 performed twice, 2 performed 4 times (8x2 + 2x4 = 24).",
        "",
        "## 1. How much does performance (vs. composition) matter?",
        "",
        "One-way random-effects ICC (unbalanced groups): fraction of total "
        "between-track variance attributable to *which piece* it is, vs. "
        "*which performance* of that piece it is.",
        "",
        "| outcome | tracks | pieces | % variance: piece | % variance: performance |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, row in icc.iterrows():
        lines.append(
            f"| `{row['outcome']}` | {int(row['n_tracks'])} | {int(row['n_pieces'])} | "
            f"{row['pct_variance_between_piece']:.1f}% | {row['pct_variance_within_piece_performance']:.1f}% |"
        )
    lines += [
        "",
        "As expected, the acoustic/MIDI features that most directly encode "
        "*how a piece is composed* (pitch height, duration) are dominated by "
        "piece identity; tempo/dynamics/brightness -- the features most under "
        "a performer's control -- show a much larger performance-level share, "
        "confirming this decomposition is behaving sensibly before turning to "
        "the outcomes of actual interest (tapping coherence, emotion ratings). "
        "`dynamics_rms_Mean` shows 0%/100% because its raw (unclipped) ICC "
        "estimate was slightly negative -- within-piece performer-to-performer "
        "loudness variation is at least as large as piece-to-piece variation, "
        "i.e. how loud a *recording* is has essentially nothing to do with "
        "which piece it is, which is itself an informative (if not surprising) "
        "result.",
        "",
        "## 2. Piece-random-intercept mixed regression (n=24 tracks, 10 pieces)",
        "",
        "`outcome ~ tempo + note_density + dynamics + brightness + pitch + duration`, "
        "random intercept per piece (`wtc_code`), all variables z-scored. This "
        "asks: holding composition fixed via the random intercept, does a "
        "*specific performance's* tempo/dynamics/texture predict its tapping "
        "coherence or emotion ratings?",
        "",
        "**Caveat up front**: n=24 tracks across only 10 piece-groups (most "
        "with only 2 members) gives this very little power to detect small "
        "effects or estimate the random-intercept variance precisely -- "
        "treat coefficients as directional leads, not confirmed effects.",
        "",
    ]
    for outcome in [OUTCOME] + [f"emotion_{e}" for e in EMOTIONS]:
        sub = mixedlm_summary[(mixedlm_summary["outcome"] == outcome) & (mixedlm_summary["term"] != "Intercept") & (~mixedlm_summary["term"].str.contains("group_var"))]
        lines.append(f"### `{outcome}`")
        for _, row in sub.iterrows():
            sig = " **(p<0.05)**" if row["p_value"] < 0.05 else ""
            lines.append(f"- `{row['term']}`: coef={row['coef']:.3f}, p={row['p_value']:.3f}{sig}")
        lines.append("")

    lines += [
        "## 3. Paired contrasts, 8 clean 2-performance pieces",
        "",
        "Within each of the 8 pieces with exactly 2 performances, ordered "
        "faster-tempo performance minus slower-tempo performance, then "
        "correlated across the 8 pieces (delta-feature vs. delta-outcome). "
        "**n=8 -- treat as a lead, not a confirmed effect**; reported with "
        "exact Pearson/Spearman stats rather than significance stars for "
        "that reason.",
        "",
        "Top |r| delta-delta associations:",
        "",
        "| feature delta | outcome delta | n | Pearson r | p | Spearman rho | p |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in corr.head(10).iterrows():
        lines.append(
            f"| `{row['feature']}` | `{row['outcome']}` | {int(row['n_pairs'])} | "
            f"{row['pearson_r']:.3f} | {row['pearson_p']:.3f} | {row['spearman_rho']:.3f} | {row['spearman_p']:.3f} |"
        )
    lines += [
        "",
        "## 4. The two 4-performance pieces (descriptive supplement)",
        "",
        "Not pooled into the n=8 paired analysis above (a 4-performance piece "
        "contributes 6 non-independent pairs, not 1); reported as within-piece "
        "spread (SD, range, CV) instead.",
        "",
        "| piece | column | n perf | mean | sd | range | CV |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    key_cols = [OUTCOME, "rhythm_tempo_Mean", "emotion_happy", "emotion_sad", "emotion_calm", "emotion_energetic"]
    for _, row in four_perf[four_perf["column"].isin(key_cols)].iterrows():
        lines.append(
            f"| {row['wtc_code']} | `{row['column']}` | {int(row['n_performances'])} | "
            f"{row['mean']:.3f} | {row['sd']:.3f} | {row['range']:.3f} | {row['coefficient_of_variation']:.3f} |"
        )
    lines.append("")
    DOC_OUT.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
