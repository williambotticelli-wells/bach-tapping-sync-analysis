#!/usr/bin/env python3
"""Join MATLAB MIRToolbox/MIDI Toolbox features into Bach multimodal tables."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


BACH_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = BACH_ROOT / "analysis"
MULTIMODAL_ROOT = ANALYSIS_ROOT / "beta_sync_multimodal"
MATLAB_ROOT = ANALYSIS_ROOT / "matlab_toolbox_features"

BASE_TABLE = MULTIMODAL_ROOT / "bach_time_binned_multimodal_table.csv"
MIR_BINNED = MATLAB_ROOT / "mirtoolbox_binned_features.csv"
MTB_BINNED = MATLAB_ROOT / "miditoolbox_binned_features.csv"
MTB_WHOLE = MATLAB_ROOT / "miditoolbox_whole_piece_features.csv"
MIR_WHOLE = MATLAB_ROOT / "mirtoolbox_whole_piece_features.csv"
MIR_STATUS = MATLAB_ROOT / "mirtoolbox_whole_piece_status.csv"

OUT_TABLE = MULTIMODAL_ROOT / "bach_time_binned_multimodal_with_matlab_toolboxes.csv"
OUT_INVENTORY = MATLAB_ROOT / "matlab_toolbox_feature_inventory.csv"


KEY_COLS = ["stim_name", "wtc_code", "window_start_s", "window_end_s", "window_center_s"]


def add_bin_keys(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["window_start_s", "window_end_s", "window_center_s"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").round(6)
    return out


def main() -> None:
    base = add_bin_keys(pd.read_csv(BASE_TABLE))
    mir = add_bin_keys(pd.read_csv(MIR_BINNED))
    mtb = add_bin_keys(pd.read_csv(MTB_BINNED))

    mir_feature_cols = [col for col in mir.columns if col.startswith("mir_")]
    mtb_feature_cols = [col for col in mtb.columns if col.startswith("mtb_")]

    joined = base.merge(
        mir[KEY_COLS + mir_feature_cols],
        on=KEY_COLS,
        how="left",
        validate="one_to_one",
    )
    joined = joined.merge(
        mtb[KEY_COLS + mtb_feature_cols],
        on=KEY_COLS,
        how="left",
        validate="one_to_one",
    )
    joined.to_csv(OUT_TABLE, index=False)

    inventory_rows = []
    for label, path, table, cols in [
        ("base_python_multimodal", BASE_TABLE, base, [c for c in base.columns if c not in KEY_COLS]),
        ("mirtoolbox_binned", MIR_BINNED, mir, mir_feature_cols),
        ("miditoolbox_binned", MTB_BINNED, mtb, mtb_feature_cols),
    ]:
        inventory_rows.append(
            {
                "source": label,
                "path": str(path),
                "n_rows": len(table),
                "n_tracks": table["stim_name"].nunique() if "stim_name" in table else "",
                "n_feature_columns": len(cols),
                "feature_columns": "|".join(cols),
            }
        )
    for label, path in [
        ("miditoolbox_whole_piece", MTB_WHOLE),
        ("mirtoolbox_whole_piece", MIR_WHOLE),
        ("mirtoolbox_whole_piece_status", MIR_STATUS),
    ]:
        table = pd.read_csv(path)
        inventory_rows.append(
            {
                "source": label,
                "path": str(path),
                "n_rows": len(table),
                "n_tracks": table["stim_name"].nunique() if "stim_name" in table else "",
                "n_feature_columns": len([c for c in table.columns if c not in {"stim_name", "wtc_code"}]),
                "feature_columns": "|".join([c for c in table.columns if c not in {"stim_name", "wtc_code"}]),
            }
        )
    inventory_rows.append(
        {
            "source": "joined_with_matlab_toolboxes",
            "path": str(OUT_TABLE),
            "n_rows": len(joined),
            "n_tracks": joined["stim_name"].nunique(),
            "n_feature_columns": len(mir_feature_cols) + len(mtb_feature_cols),
            "feature_columns": "|".join(mir_feature_cols + mtb_feature_cols),
        }
    )
    pd.DataFrame(inventory_rows).to_csv(OUT_INVENTORY, index=False)
    print(f"Wrote {OUT_TABLE}")
    print(f"Wrote {OUT_INVENTORY}")
    print(f"Rows: base={len(base)} joined={len(joined)}")
    print(f"Tracks: {joined['stim_name'].nunique()}")
    print(f"Added MATLAB columns: {len(mir_feature_cols) + len(mtb_feature_cols)}")


if __name__ == "__main__":
    main()
