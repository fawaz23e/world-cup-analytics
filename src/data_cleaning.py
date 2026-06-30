"""
data_cleaning.py
-----------------
Reproducible cleaning pipeline for the World Cup Analytics project.

This module loads the four raw CSV files shipped in ``data/raw/`` and
produces validated, analysis-ready DataFrames. Raw files are never
modified in place; cleaned outputs are written to ``data/processed/``
by the caller (see notebooks/01_data_audit_and_cleaning.ipynb).

Design decisions (documented, not hidden):
* We do NOT merge historical national teams into their modern successor
  by default (e.g. we keep "Czechoslovakia" separate from "Czech Republic").
  Forcing that merge would conflate squads, eras, and political entities
  that are not meaningfully comparable. ``former_names.csv`` is loaded
  and exposed as a reference table so a reader can perform that mapping
  explicitly if a specific question requires it, but no automatic
  aggregation is applied.
* Rows with missing scores are treated as *unplayed / scheduled*
  fixtures (this is exactly what the 2026 World Cup rows turn out to be)
  and are dropped from match-level analysis, never imputed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

RAW_FILES = {
    "results": RAW_DIR / "results.csv",
    "goalscorers": RAW_DIR / "goalscorers.csv",
    "shootouts": RAW_DIR / "shootouts.csv",
    "former_names": RAW_DIR / "former_names.csv",
}


def _require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"Required raw data file is missing: {path}. "
            "Make sure the repository's data/raw/ directory is intact."
        )


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_raw() -> Dict[str, pd.DataFrame]:
    """Load all four raw CSVs into a dict of DataFrames, unmodified."""
    frames = {}
    for name, path in RAW_FILES.items():
        _require_file(path)
        frames[name] = pd.read_csv(path)
    return frames


# ---------------------------------------------------------------------------
# Cleaning: results.csv (match level)
# ---------------------------------------------------------------------------

def clean_results(results: pd.DataFrame) -> pd.DataFrame:
    """Clean the match-level results table.

    Steps:
    1. Standardize column names (already snake_case in source, kept as-is).
    2. Parse ``date`` as a real datetime.
    3. Validate score columns are non-negative where present.
    4. Drop rows with missing scores (unplayed/scheduled fixtures) and
       record how many were dropped.
    5. Standardize the ``neutral`` boolean column.
    6. Remove exact duplicate rows.
    7. Flag (but do not silently drop) rows that share date/home/away but
       differ elsewhere -- these are investigated, not auto-removed.
    """
    df = results.copy()
    required_cols = {
        "date",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
        "tournament",
        "city",
        "country",
        "neutral",
    }
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"results.csv is missing expected columns: {missing_cols}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    n_bad_dates = df["date"].isna().sum()
    if n_bad_dates:
        df = df.dropna(subset=["date"])

    # Drop exact duplicate rows.
    n_before = len(df)
    df = df.drop_duplicates()
    n_exact_dupes = n_before - len(df)

    # Unplayed / scheduled fixtures: no recorded score.
    n_unplayed = int(df["home_score"].isna().sum())
    df_played = df.dropna(subset=["home_score", "away_score"]).copy()

    # Validate non-negative scores.
    df_played["home_score"] = df_played["home_score"].astype(int)
    df_played["away_score"] = df_played["away_score"].astype(int)
    negative_scores = (df_played["home_score"] < 0) | (df_played["away_score"] < 0)
    if negative_scores.any():
        raise ValueError(
            f"Found {negative_scores.sum()} rows with a negative score; "
            "refusing to silently clip them."
        )

    # Standardize neutral flag to boolean.
    df_played["neutral"] = df_played["neutral"].astype(bool)

    # Require non-null team names.
    df_played = df_played[df_played["home_team"].notna() & df_played["away_team"].notna()]

    # Every match must have a determinate outcome (home/away/draw) given
    # valid integer scores -- guaranteed by construction here, but assert
    # it explicitly as a data-quality contract.
    assert df_played["home_score"].notna().all()
    assert df_played["away_score"].notna().all()

    df_played = df_played.sort_values("date").reset_index(drop=True)

    df_played.attrs["cleaning_log"] = {
        "rows_in_raw": int(n_before + n_bad_dates),
        "rows_with_unparseable_dates_dropped": int(n_bad_dates),
        "exact_duplicate_rows_dropped": int(n_exact_dupes),
        "unplayed_or_scheduled_rows_dropped": int(n_unplayed),
        "rows_remaining_played_matches": int(len(df_played)),
    }
    return df_played


def find_conflicting_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Return rows that share (date, home_team, away_team) but disagree on
    score or other fields -- these are NOT exact duplicates and are
    surfaced for manual review rather than being dropped automatically.
    """
    key = ["date", "home_team", "away_team"]
    dup_mask = df.duplicated(subset=key, keep=False)
    return df[dup_mask].sort_values(key)


# ---------------------------------------------------------------------------
# Cleaning: goalscorers.csv
# ---------------------------------------------------------------------------

def clean_goalscorers(goalscorers: pd.DataFrame) -> pd.DataFrame:
    """Clean the goalscorer event-level table."""
    df = goalscorers.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "home_team", "away_team", "team"])
    df["own_goal"] = df["own_goal"].astype(bool)
    df["penalty"] = df["penalty"].astype(bool)
    # `minute` and `scorer` may legitimately be missing (e.g. minute not
    # recorded for very old matches) -- we keep these rows but flag them
    # rather than dropping potentially valid goal events.
    df["minute_missing"] = df["minute"].isna()
    df["scorer_missing"] = df["scorer"].isna()
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Cleaning: shootouts.csv
# ---------------------------------------------------------------------------

def clean_shootouts(shootouts: pd.DataFrame) -> pd.DataFrame:
    """Clean the penalty-shootout outcomes table."""
    df = shootouts.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "home_team", "away_team", "winner"])
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Cleaning: former_names.csv
# ---------------------------------------------------------------------------

def clean_former_names(former_names: pd.DataFrame) -> pd.DataFrame:
    """Clean the historical team-name reference table.

    This table is retained purely as documentation / an optional lookup.
    It is intentionally NOT applied automatically to results.csv -- see
    module docstring for the reasoning.
    """
    df = former_names.copy()
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_match_data(df: pd.DataFrame) -> Dict[str, bool]:
    """Run the data-quality contract checks required by the project spec."""
    checks = {
        "no_negative_scores": bool(((df["home_score"] >= 0) & (df["away_score"] >= 0)).all()),
        "home_and_away_teams_present": bool(df["home_team"].notna().all() and df["away_team"].notna().all()),
        "dates_valid": bool(df["date"].notna().all()),
        "every_match_has_outcome": bool(
            (df["home_score"].notna() & df["away_score"].notna()).all()
        ),
        "no_exact_duplicates": bool(not df.duplicated().any()),
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise AssertionError(f"Data validation failed for: {failed}")
    return checks


def save_processed(frames: Dict[str, pd.DataFrame]) -> None:
    """Write cleaned frames to data/processed/, creating the dir if needed."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in frames.items():
        df.to_csv(PROCESSED_DIR / f"{name}_clean.csv", index=False)


def run_cleaning_pipeline() -> Dict[str, pd.DataFrame]:
    """End-to-end cleaning entry point used by notebooks and scripts."""
    raw = load_raw()
    results_clean = clean_results(raw["results"])
    validate_match_data(results_clean)
    goalscorers_clean = clean_goalscorers(raw["goalscorers"])
    shootouts_clean = clean_shootouts(raw["shootouts"])
    former_names_clean = clean_former_names(raw["former_names"])

    cleaned = {
        "results": results_clean,
        "goalscorers": goalscorers_clean,
        "shootouts": shootouts_clean,
        "former_names": former_names_clean,
    }
    save_processed(cleaned)
    return cleaned


if __name__ == "__main__":
    cleaned = run_cleaning_pipeline()
    for name, df in cleaned.items():
        print(f"{name}: {df.shape}")
    print("Cleaning log:", cleaned["results"].attrs.get("cleaning_log"))
