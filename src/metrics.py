"""
metrics.py
----------
Team performance metrics, the Team Dominance Index, and the World Cup
Consistency Score.

All ranking logic here is intentionally transparent: every weight and
threshold is a named constant, not a magic number buried in a formula.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

# Default weights for the Team Dominance Index (Phase 8 starting point).
DEFAULT_WEIGHTS = {
    "win_rate": 0.25,
    "avg_goal_diff": 0.25,
    "points_per_match": 0.20,
    "dominant_win_rate": 0.15,
    "consistency": 0.15,
}

EQUAL_WEIGHTS = {k: 1 / len(DEFAULT_WEIGHTS) for k in DEFAULT_WEIGHTS}

# "Performance-heavy" alternative: weight raw scoring performance
# (goal differential, points) more than win/loss binaries.
PERFORMANCE_HEAVY_WEIGHTS = {
    "win_rate": 0.15,
    "avg_goal_diff": 0.35,
    "points_per_match": 0.30,
    "dominant_win_rate": 0.10,
    "consistency": 0.10,
}


def team_summary(team_df: pd.DataFrame, min_matches: int = 1) -> pd.DataFrame:
    """Aggregate the exploded team-level table into one row per team."""
    g = team_df.groupby("team")
    summary = g.agg(
        matches_played=("team", "size"),
        wins=("win", "sum"),
        draws=("draw", "sum"),
        losses=("loss", "sum"),
        goals_scored=("goals_for", "sum"),
        goals_conceded=("goals_against", "sum"),
        total_goal_differential=("goal_difference", "sum"),
        points=("points", "sum"),
        dominant_wins=("dominant_win", "sum"),
    ).reset_index()

    summary["win_rate"] = summary["wins"] / summary["matches_played"]
    summary["draw_rate"] = summary["draws"] / summary["matches_played"]
    summary["loss_rate"] = summary["losses"] / summary["matches_played"]
    summary["avg_goal_diff"] = summary["total_goal_differential"] / summary["matches_played"]
    summary["goals_scored_per_match"] = summary["goals_scored"] / summary["matches_played"]
    summary["goals_conceded_per_match"] = summary["goals_conceded"] / summary["matches_played"]
    summary["points_per_match"] = summary["points"] / summary["matches_played"]
    summary["dominant_win_rate"] = summary["dominant_wins"] / summary["matches_played"]

    summary = summary[summary["matches_played"] >= min_matches].reset_index(drop=True)
    return summary.sort_values("points_per_match", ascending=False).reset_index(drop=True)


def world_cup_tournament_summary(wc_team_df: pd.DataFrame) -> pd.DataFrame:
    """Team-by-tournament World Cup summary (one row per team per WC year)."""
    g = wc_team_df.groupby(["team", "world_cup_year"])
    out = g.agg(
        matches_played=("team", "size"),
        wins=("win", "sum"),
        draws=("draw", "sum"),
        losses=("loss", "sum"),
        goals_scored=("goals_for", "sum"),
        goals_conceded=("goals_against", "sum"),
        goal_difference=("goal_difference", "sum"),
        points=("points", "sum"),
        dominant_wins=("dominant_win", "sum"),
    ).reset_index()
    out["points_per_match"] = out["points"] / out["matches_played"]
    return out.sort_values(["world_cup_year", "points"], ascending=[True, False]).reset_index(drop=True)


def consistency_score(tournament_summary: pd.DataFrame, min_tournaments: int = 2) -> pd.DataFrame:
    """World Cup Consistency Score per Phase 9.

    Formula (documented for interview discussion):

        consistency = 0.5 * mean_points_per_match_normalized
                    + 0.3 * pct_tournaments_positive_goal_diff
                    - 0.2 * std_points_per_match_normalized
        then scaled to participation: multiply by min(1, n_tournaments / 3)

    Rationale: a team that is consistently solid (high mean PPM, usually
    positive goal difference, low variance across tournaments) scores
    higher. The participation scaler penalizes teams that only ever
    qualified once or twice -- one good tournament is a data point, not a
    track record. Teams with fewer than ``min_tournaments`` World Cup
    appearances are excluded entirely, since a single tournament has no
    variance to measure and would be misleadingly labeled "consistent."
    """
    g = tournament_summary.groupby("team")
    per_team = g.agg(
        n_tournaments=("world_cup_year", "nunique"),
        mean_ppm=("points_per_match", "mean"),
        std_ppm=("points_per_match", "std"),
        pct_positive_gd=("goal_difference", lambda s: (s > 0).mean()),
    ).reset_index()
    per_team = per_team[per_team["n_tournaments"] >= min_tournaments].copy()
    per_team["std_ppm"] = per_team["std_ppm"].fillna(0)

    def _minmax(s: pd.Series) -> pd.Series:
        rng = s.max() - s.min()
        if rng == 0:
            return pd.Series(0.5, index=s.index)
        return (s - s.min()) / rng

    mean_ppm_norm = _minmax(per_team["mean_ppm"])
    std_ppm_norm = _minmax(per_team["std_ppm"])

    participation_scaler = np.minimum(1.0, per_team["n_tournaments"] / 3.0)

    raw_consistency = (
        0.5 * mean_ppm_norm
        + 0.3 * per_team["pct_positive_gd"]
        - 0.2 * std_ppm_norm
    )
    per_team["consistency_score"] = raw_consistency * participation_scaler
    # Re-scale final scores to 0-1 for interpretability.
    per_team["consistency_score"] = _minmax(per_team["consistency_score"])
    return per_team.sort_values("consistency_score", ascending=False).reset_index(drop=True)


def _zscore(s: pd.Series) -> pd.Series:
    std = s.std(ddof=0)
    if std == 0:
        return pd.Series(0.0, index=s.index)
    return (s - s.mean()) / std


def _minmax(s: pd.Series) -> pd.Series:
    rng = s.max() - s.min()
    if rng == 0:
        return pd.Series(0.5, index=s.index)
    return (s - s.min()) / rng


def team_dominance_index(
    summary: pd.DataFrame,
    consistency: pd.DataFrame,
    weights: dict = None,
    min_matches: int = 30,
    normalization: str = "minmax",
) -> pd.DataFrame:
    """Compute the Team Dominance Index.

    We use min-max normalization by default (not z-scores) because the
    index is meant to be read on an intuitive 0-1 scale by a non-technical
    audience (e.g. in a dashboard); z-scores are unbounded and
    harder to interpret at a glance. Both are valid -- z-score is offered
    via ``normalization="zscore"`` for comparison.

    ``min_matches`` defaults to 30 so teams with a handful of friendlies
    do not get inflated win/dominant-win rates from tiny samples.
    """
    weights = weights or DEFAULT_WEIGHTS
    df = summary[summary["matches_played"] >= min_matches].copy()
    df = df.merge(consistency[["team", "consistency_score"]], on="team", how="left")
    df["consistency_score"] = df["consistency_score"].fillna(0.0)  # no WC history -> 0, not dropped

    norm_fn = _minmax if normalization == "minmax" else _zscore

    df["n_win_rate"] = norm_fn(df["win_rate"])
    df["n_avg_goal_diff"] = norm_fn(df["avg_goal_diff"])
    df["n_points_per_match"] = norm_fn(df["points_per_match"])
    df["n_dominant_win_rate"] = norm_fn(df["dominant_win_rate"])
    df["n_consistency"] = norm_fn(df["consistency_score"])

    df["dominance_index"] = (
        weights["win_rate"] * df["n_win_rate"]
        + weights["avg_goal_diff"] * df["n_avg_goal_diff"]
        + weights["points_per_match"] * df["n_points_per_match"]
        + weights["dominant_win_rate"] * df["n_dominant_win_rate"]
        + weights["consistency"] * df["n_consistency"]
    )
    if normalization == "minmax":
        df["dominance_index"] = _minmax(df["dominance_index"]) * 100  # 0-100 scale

    return df.sort_values("dominance_index", ascending=False).reset_index(drop=True)
