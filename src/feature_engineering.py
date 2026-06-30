"""
feature_engineering.py
-----------------------
Builds match-level and team-level feature tables from the cleaned
results data, plus the FIFA men's World Cup final-tournament filter.

A "dominant win" defaults to a margin of >= 3 goals (configurable via
the ``dominant_margin`` parameter so Phase 8 sensitivity analysis can
re-run with margins of 2 and 4).
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Tournament names in results.csv that represent FIFA MEN'S World Cup
# *final tournament* matches. Everything else containing the phrase
# "World Cup" (qualification, Viva World Cup, etc.) is deliberately
# excluded -- see notebooks/03_world_cup_analysis.ipynb for the audit
# of every tournament name in the raw data.
FIFA_MENS_WORLD_CUP_FINALS = "FIFA World Cup"

WORLD_CUP_YEARS_SINCE_2002 = [2002, 2006, 2010, 2014, 2018, 2022]


def add_match_features(df: pd.DataFrame, dominant_margin: int = 3) -> pd.DataFrame:
    """Add match-level derived columns to a cleaned results DataFrame."""
    out = df.copy()
    if "match_id" not in out.columns:
        out.insert(0, "match_id", range(1, len(out) + 1))
    out["year"] = out["date"].dt.year
    out["decade"] = (out["year"] // 10) * 10
    out["total_goals"] = out["home_score"] + out["away_score"]
    out["goal_difference"] = out["home_score"] - out["away_score"]
    out["absolute_goal_difference"] = out["goal_difference"].abs()

    out["match_result"] = np.where(
        out["goal_difference"] > 0, "home_win",
        np.where(out["goal_difference"] < 0, "away_win", "draw"),
    )
    out["is_draw"] = out["match_result"] == "draw"
    out["home_win"] = out["match_result"] == "home_win"
    out["away_win"] = out["match_result"] == "away_win"

    out["winner"] = np.where(
        out["home_win"], out["home_team"],
        np.where(out["away_win"], out["away_team"], np.nan),
    )
    out["loser"] = np.where(
        out["home_win"], out["away_team"],
        np.where(out["away_win"], out["home_team"], np.nan),
    )

    out["dominant_win"] = out["absolute_goal_difference"] >= dominant_margin
    out["neutral_match"] = out["neutral"].astype(bool)

    out["is_world_cup"] = out["tournament"] == FIFA_MENS_WORLD_CUP_FINALS
    out["world_cup_year"] = out["year"].where(out["is_world_cup"]).astype("Int64")

    def _category(t: str) -> str:
        tl = t.lower()
        if t == FIFA_MENS_WORLD_CUP_FINALS:
            return "World Cup (final tournament)"
        if "world cup qualification" in tl:
            return "World Cup qualification"
        if "friendly" in tl:
            return "Friendly"
        if "cup of nations" in tl or "championship" in tl or "copa" in tl:
            return "Continental competition"
        return "Other"

    out["tournament_category"] = out["tournament"].apply(_category)

    return out


def build_team_level(df: pd.DataFrame) -> pd.DataFrame:
    """Explode each match into two team-perspective rows (home + away)."""
    home = pd.DataFrame({
        "match_id": df["match_id"],
        "date": df["date"],
        "team": df["home_team"],
        "opponent": df["away_team"],
        "tournament": df["tournament"],
        "tournament_category": df["tournament_category"],
        "home_or_away": "home",
        "neutral": df["neutral_match"],
        "goals_for": df["home_score"],
        "goals_against": df["away_score"],
        "is_world_cup": df["is_world_cup"],
        "world_cup_year": df["world_cup_year"],
        "year": df["year"],
        "dominant_win": df["home_win"] & df["dominant_win"],
    })
    away = pd.DataFrame({
        "match_id": df["match_id"],
        "date": df["date"],
        "team": df["away_team"],
        "opponent": df["home_team"],
        "tournament": df["tournament"],
        "tournament_category": df["tournament_category"],
        "home_or_away": "away",
        "neutral": df["neutral_match"],
        "goals_for": df["away_score"],
        "goals_against": df["home_score"],
        "is_world_cup": df["is_world_cup"],
        "world_cup_year": df["world_cup_year"],
        "year": df["year"],
        "dominant_win": df["away_win"] & df["dominant_win"],
    })
    team_level = pd.concat([home, away], ignore_index=True)
    team_level["goal_difference"] = team_level["goals_for"] - team_level["goals_against"]

    team_level["result"] = np.where(
        team_level["goal_difference"] > 0, "win",
        np.where(team_level["goal_difference"] < 0, "loss", "draw"),
    )
    team_level["win"] = team_level["result"] == "win"
    team_level["draw"] = team_level["result"] == "draw"
    team_level["loss"] = team_level["result"] == "loss"
    team_level["points"] = np.select(
        [team_level["win"], team_level["draw"], team_level["loss"]],
        [3, 1, 0],
    )

    ordered_columns = [
        "match_id",
        "date",
        "team",
        "opponent",
        "tournament",
        "tournament_category",
        "home_or_away",
        "neutral",
        "goals_for",
        "goals_against",
        "is_world_cup",
        "world_cup_year",
        "year",
        "goal_difference",
        "result",
        "win",
        "draw",
        "loss",
        "points",
        "dominant_win",
    ]
    team_level = team_level[ordered_columns]
    team_level = team_level.sort_values(["date", "match_id", "team"]).reset_index(drop=True)
    return team_level


def validate_team_level(match_df: pd.DataFrame, team_df: pd.DataFrame) -> dict:
    """Reconciliation checks between match-level and team-level tables."""
    checks = {}
    checks["two_rows_per_match"] = (len(team_df) == 2 * len(match_df))
    checks["each_match_id_has_two_rows"] = bool((team_df.groupby("match_id").size() == 2).all())

    mutually_exclusive = ((team_df["win"].astype(int) + team_df["draw"].astype(int)
                            + team_df["loss"].astype(int)) == 1).all()
    checks["win_draw_loss_mutually_exclusive"] = bool(mutually_exclusive)
    checks["points_match_result"] = bool(
        team_df["points"].eq(
            np.select([team_df["win"], team_df["draw"], team_df["loss"]], [3, 1, 0])
        ).all()
    )

    total_goals_for = team_df["goals_for"].sum()
    total_goals_against = team_df["goals_against"].sum()
    checks["goals_for_equals_goals_against_aggregate"] = bool(total_goals_for == total_goals_against)

    total_wins = team_df["win"].sum()
    total_losses = team_df["loss"].sum()
    checks["wins_equal_losses_count"] = bool(total_wins == total_losses)

    expected_match_goals = (match_df["home_score"].sum() + match_df["away_score"].sum())
    checks["team_level_goal_total_matches_match_level"] = bool(total_goals_for == expected_match_goals)

    home_rows = team_df[team_df["home_or_away"] == "home"].set_index("match_id")
    away_rows = team_df[team_df["home_or_away"] == "away"].set_index("match_id")
    matches = match_df.set_index("match_id")
    checks["one_home_and_one_away_row_per_match"] = bool(
        home_rows.index.is_unique
        and away_rows.index.is_unique
        and set(home_rows.index) == set(matches.index)
        and set(away_rows.index) == set(matches.index)
    )
    checks["home_goals_reconcile"] = bool(
        home_rows.loc[matches.index, "goals_for"].to_numpy().tolist()
        == matches["home_score"].to_numpy().tolist()
    )
    checks["away_goals_reconcile"] = bool(
        away_rows.loc[matches.index, "goals_for"].to_numpy().tolist()
        == matches["away_score"].to_numpy().tolist()
    )
    checks["opponent_goals_reconcile"] = bool(
        (
            home_rows.loc[matches.index, "goals_for"].to_numpy()
            == away_rows.loc[matches.index, "goals_against"].to_numpy()
        ).all()
        and (
            away_rows.loc[matches.index, "goals_for"].to_numpy()
            == home_rows.loc[matches.index, "goals_against"].to_numpy()
        ).all()
    )
    checks["paired_results_reconcile"] = bool(
        (team_df.groupby("match_id")["goal_difference"].sum() == 0).all()
        and (team_df.groupby("match_id")["win"].sum() == team_df.groupby("match_id")["loss"].sum()).all()
    )

    failed = [k for k, v in checks.items() if not v]
    if failed:
        raise AssertionError(f"Team-level validation failed for: {failed}")
    return checks


def filter_world_cup_since_2002(match_df: pd.DataFrame) -> pd.DataFrame:
    """Isolate FIFA men's World Cup final-tournament matches from 2002
    onward. Explicitly excludes 2026 because, in this dataset, the 2026
    rows have no recorded scores (they are scheduled fixtures, not played
    matches) -- they were already dropped in cleaning, but we double the
    guard here for clarity and safety.
    """
    wc = match_df[match_df["is_world_cup"] & (match_df["year"] >= 2002)].copy()
    wc = wc[wc["year"] != 2026]
    return wc


if __name__ == "__main__":
    from data_cleaning import run_cleaning_pipeline

    cleaned = run_cleaning_pipeline()
    matches = add_match_features(cleaned["results"])
    teams = build_team_level(matches)
    checks = validate_team_level(matches, teams)
    print("Validation checks:", checks)
    wc = filter_world_cup_since_2002(matches)
    print("World Cup matches since 2002:", len(wc))
    print("World Cup years present:", sorted(wc["year"].unique()))

    PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
    matches.to_csv(PROCESSED_DIR / "matches_features.csv", index=False)
    teams.to_csv(PROCESSED_DIR / "team_level.csv", index=False)
    wc.to_csv(PROCESSED_DIR / "world_cup_matches_2002_2022.csv", index=False)
