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

def insert_records(sheet_name, updates_df: pd.DataFrame):
    """
    Insert all rows from `updates_df` into the Excel 'base' sheet.
    """

    # Read current sheet
    if("application" in sheet_name):
        cols, base = read_application_tracker_file(sheet_name)
    elif("meet" in sheet_name):
        cols, base = read_meet_tracker_file(sheet_name)
        
    updates_df = updates_df.copy()[cols]

    # Append directly
    out_df = pd.concat([base, updates_df], axis=0, ignore_index=True)

    # Save back to the same file and sheet
    try:
        with pd.ExcelWriter(f"{path}/data/tracker.xlsx", engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            out_df.to_excel(writer, sheet_name=sheet_name, index=False)
    except FileNotFoundError:
        # If file doesn't exist yet, create it
        with pd.ExcelWriter(f"{path}/data/tracker.xlsx", engine="openpyxl", mode="w") as writer:
            out_df.to_excel(writer, sheet_name=sheet_name, index=False)



def read_application_tracker_file(sheet_name):
    """
    Reads the base Excel, normalizes headers, and returns:
    """
    # Read (keep job_id as string so leading zeros aren’t lost)
    df = pd.read_excel(f"{path}/data/tracker.xlsx", sheet_name=sheet_name)

    # Required columns
    cols = ["company_name", "job_title", "job_id", "application_status", "sent_by", "sender_email", "email_sent_date"]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {Path(path).name}: {missing}")

    # Return only needed columns, drop empty key rows
    return cols, df[cols].dropna(subset=["company_name"]).reset_index(drop=True)


def read_meet_tracker_file(sheet_name):
    """
    Reads the base Excel, normalizes headers, and returns:
    """
    # Read (keep job_id as string so leading zeros aren’t lost)
    df = pd.read_excel(f"{path}/data/tracker.xlsx", sheet_name=sheet_name)

    # Required columns
    cols = ["sender_email", "request_sent_by", "mail_sent_date", "requested_date_time", "reason_for_meeting"]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {Path(path).name}: {missing}")

    # Return only needed columns, drop empty key rows
    return cols, df[cols].dropna(subset=["request_sent_by"]).reset_index(drop=True)

