# -----------------------------
# IMPORTING LIBRARIES
# -----------------------------

import pandas as pd
import os
import sys
from pathlib import Path

# -----------------------------
# SETTING UP PATH
# -----------------------------

path = Path(os.path.dirname(os.getcwd()))
path = str(path)
sys.path.insert(1, path)

# -----------------------------
# IMPORTING FUNCTIONS
# -----------------------------

def upsert_applications(sheet_name, updates_df: pd.DataFrame,
                        overwrite: bool = True):
    """
    Upsert rows from `updates_df` into the Excel 'base' sheet using
    ['company_name','job_title'] as the composite key, then save back
    to the same file/sheet.

    Columns: ['company_name','job_title','job_id','application_status']
    - overwrite=True: replace entire matching rows
    - overwrite=False: update only where incoming has non-null values
    """
    cols = ["company_name", "job_title", "job_id", "application_status"]

    # Read current sheet
    base = read_tracker_file(sheet_name)
    updates_df = updates_df.copy()[cols]

    # If updates_df has duplicate keys, keep the last one
    updates_df = updates_df.drop_duplicates(
        subset=["company_name", "job_title"], keep="last"
    )

    # Composite index for clean upsert
    base_i    = base.set_index(["company_name", "job_title"])
    updates_i = updates_df.set_index(["company_name", "job_title"])

    out = base_i.copy()

    # ---- UPDATE (existing keys) ----
    if overwrite:
        common = out.index.intersection(updates_i.index)
        out.loc[common] = updates_i.loc[common]
    else:
        out.update(updates_i)  # only non-null values from updates_df overwrite

    # ---- INSERT (new keys) ----
    new_only = updates_i.index.difference(out.index)
    out = pd.concat([out, updates_i.loc[new_only]], axis=0)

    # Final DataFrame
    out_df = out.reset_index()

    # ---- SAVE back to the same file and sheet ----
    # assumes global variable `path` points to the Excel file
    try:
        with pd.ExcelWriter(f"{path}/data/application_tracker.xlsx", engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            out_df.to_excel(writer, sheet_name=sheet_name, index=False)
    except FileNotFoundError:
        # If file doesn't exist yet, create it
        with pd.ExcelWriter(f"{path}/data/application_tracker.xlsx", engine="openpyxl", mode="w") as writer:
            out_df.to_excel(writer, sheet_name=sheet_name, index=False)



def read_tracker_file(sheet_name="tracker"):
    """
    Reads the base Excel, normalizes headers, and returns:
    ['company_name','job_title','job_id','application_status']
    """
    # Read (keep job_id as string so leading zeros aren’t lost)
    df = pd.read_excel(f"{path}/data/application_tracker.xlsx", sheet_name=sheet_name)

    # Required columns
    cols = ["company_name", "job_title", "job_id", "application_status"]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {Path(path).name}: {missing}")

    # Return only needed columns, drop empty key rows
    return (df[cols]
            .dropna(subset=["company_name"])
            .reset_index(drop=True))

