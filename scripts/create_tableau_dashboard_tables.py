"""Create Tableau-specific dashboard summary tables.

These tables keep the packaged Tableau workbook simple and stable by moving
headline metrics, scorer aggregation, and Elo calculations into reproducible
CSV outputs before the Hyper extract is built.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def _result_score(home_score: int, away_score: int) -> float:
    if home_score > away_score:
        return 1.0
    if home_score == away_score:
        return 0.5
    return 0.0


def build_elo_rankings(matches: pd.DataFrame) -> pd.DataFrame:
    ratings: dict[str, float] = {}
    records: dict[str, dict[str, object]] = {}

    matches = matches.sort_values(["date", "match_id"]).copy()
    for _, row in matches.iterrows():
        home = row["home_team"]
        away = row["away_team"]
        home_score = int(row["home_score"])
        away_score = int(row["away_score"])

        home_rating = ratings.get(home, 1500.0)
        away_rating = ratings.get(away, 1500.0)
        expected_home = 1 / (1 + 10 ** ((away_rating - home_rating) / 400))
        actual_home = _result_score(home_score, away_score)
        margin = abs(home_score - away_score)
        margin_multiplier = 1 + min(margin, 4) * 0.10
        adjustment = 30 * margin_multiplier * (actual_home - expected_home)

        ratings[home] = home_rating + adjustment
        ratings[away] = away_rating - adjustment

        for team, goals_for, goals_against in [
            (home, home_score, away_score),
            (away, away_score, home_score),
        ]:
            if team not in records:
                records[team] = {
                    "team": team,
                    "matches_played": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "goals_for": 0,
                    "goals_against": 0,
                    "last_match_date": None,
                }
            rec = records[team]
            rec["matches_played"] = int(rec["matches_played"]) + 1
            rec["goals_for"] = int(rec["goals_for"]) + goals_for
            rec["goals_against"] = int(rec["goals_against"]) + goals_against
            rec["last_match_date"] = row["date"]
            if goals_for > goals_against:
                rec["wins"] = int(rec["wins"]) + 1
            elif goals_for == goals_against:
                rec["draws"] = int(rec["draws"]) + 1
            else:
                rec["losses"] = int(rec["losses"]) + 1

    elo = pd.DataFrame(records.values())
    elo["elo_rating"] = elo["team"].map(ratings).round(1)
    elo["goal_difference"] = elo["goals_for"] - elo["goals_against"]
    elo = elo.sort_values(["elo_rating", "matches_played"], ascending=[False, False])
    elo.insert(0, "elo_rank", range(1, len(elo) + 1))
    elo["elo_label"] = elo["elo_rank"].astype(str) + ". " + elo["team"]
    return elo[
        [
            "elo_rank",
            "elo_label",
            "team",
            "elo_rating",
            "matches_played",
            "wins",
            "draws",
            "losses",
            "goals_for",
            "goals_against",
            "goal_difference",
            "last_match_date",
        ]
    ]


def build_top_scorers(goals: pd.DataFrame) -> pd.DataFrame:
    goals = goals.copy()
    goals["goal_count"] = 1
    scorers = (
        goals.groupby(["scorer", "team"], dropna=False)
        .agg(
            goals=("goal_count", "sum"),
            penalties=("penalty", "sum"),
            own_goals=("own_goal", "sum"),
            first_goal_date=("date", "min"),
            latest_goal_date=("date", "max"),
        )
        .reset_index()
        .sort_values(["goals", "penalties", "latest_goal_date"], ascending=[False, False, False])
    )
    scorers.insert(0, "scorer_rank", range(1, len(scorers) + 1))
    scorers["scorer_label"] = scorers["scorer_rank"].astype(str) + ". " + scorers["scorer"]
    return scorers


def build_dashboard_kpis(
    matches: pd.DataFrame,
    world_cup_matches: pd.DataFrame,
    goals: pd.DataFrame,
    elo: pd.DataFrame,
) -> pd.DataFrame:
    top_scorer = (
        goals.assign(goal_count=1)
        .groupby("scorer", dropna=False)["goal_count"]
        .sum()
        .sort_values(ascending=False)
        .head(1)
    )
    top_scorer_name = str(top_scorer.index[0])
    top_scorer_goals = int(top_scorer.iloc[0])
    top_elo_team = elo.iloc[0]

    kpis = [
        ("Matches", len(matches), f"{len(matches):,}", 1),
        ("Teams", pd.concat([matches["home_team"], matches["away_team"]]).nunique(), f"{pd.concat([matches['home_team'], matches['away_team']]).nunique():,}", 2),
        ("World Cup Matches", len(world_cup_matches), f"{len(world_cup_matches):,}", 3),
        ("Goals", int(matches["total_goals"].sum()), f"{int(matches['total_goals'].sum()):,}", 4),
        ("Top Elo Team", float(top_elo_team["elo_rating"]), f"{top_elo_team['team']} ({top_elo_team['elo_rating']:.1f})", 5),
        ("Top Scorer", top_scorer_goals, f"{top_scorer_name} ({top_scorer_goals:,})", 6),
    ]
    return pd.DataFrame(kpis, columns=["kpi_label", "kpi_value", "kpi_display", "sort_order"])


def build_world_cup_scoring_trend(world_cup_matches: pd.DataFrame) -> pd.DataFrame:
    trend = (
        world_cup_matches.groupby("world_cup_year", as_index=False)
        .agg(
            matches=("match_id", "count"),
            total_goals=("total_goals", "sum"),
            avg_goals_per_match=("total_goals", "mean"),
        )
        .sort_values("world_cup_year")
    )
    trend["avg_goals_per_match"] = trend["avg_goals_per_match"].round(2)
    return trend


def build_world_cup_points_top_10(root: Path) -> pd.DataFrame:
    summary = pd.read_csv(root / "outputs" / "tables" / "team_summary_world_cup_2002_2022.csv")
    summary = summary.sort_values(
        ["points_per_match", "matches_played"], ascending=[False, False]
    ).head(10)
    summary.insert(0, "points_rank", range(1, len(summary) + 1))
    summary["points_label"] = summary["points_rank"].astype(str) + ". " + summary["team"]
    return summary


def build_team_dominance_top_10(root: Path) -> pd.DataFrame:
    dominance = pd.read_csv(root / "outputs" / "tables" / "team_dominance_index_main.csv")
    dominance = dominance.sort_values("dominance_index", ascending=False).head(10)
    dominance.insert(0, "dominance_rank", range(1, len(dominance) + 1))
    dominance["dominance_label"] = dominance["dominance_rank"].astype(str) + ". " + dominance["team"]
    return dominance


def build_tableau_dashboard_tables(root: Path | None = None) -> None:
    root = root or Path(__file__).resolve().parents[1]
    outputs = root / "outputs" / "tables"
    outputs.mkdir(parents=True, exist_ok=True)

    matches = pd.read_csv(root / "data" / "processed" / "matches_features.csv", parse_dates=["date"])
    world_cup_matches = pd.read_csv(root / "data" / "processed" / "world_cup_matches_2002_2022.csv")
    goals = pd.read_csv(root / "data" / "processed" / "goalscorers_clean.csv", parse_dates=["date"])

    elo = build_elo_rankings(matches)
    top_scorers = build_top_scorers(goals)
    kpis = build_dashboard_kpis(matches, world_cup_matches, goals, elo)
    scoring_trend = build_world_cup_scoring_trend(world_cup_matches)
    points_top_10 = build_world_cup_points_top_10(root)
    dominance_top_10 = build_team_dominance_top_10(root)

    elo["last_match_date"] = pd.to_datetime(elo["last_match_date"]).dt.date
    top_scorers["first_goal_date"] = pd.to_datetime(top_scorers["first_goal_date"]).dt.date
    top_scorers["latest_goal_date"] = pd.to_datetime(top_scorers["latest_goal_date"]).dt.date

    elo.to_csv(outputs / "elo_rankings.csv", index=False)
    elo.head(10).to_csv(outputs / "elo_top_10.csv", index=False)
    elo.head(25).to_csv(outputs / "elo_top_25.csv", index=False)
    top_scorers.to_csv(outputs / "top_scorers_summary.csv", index=False)
    top_scorers.head(10).to_csv(outputs / "top_scorers_top_10.csv", index=False)
    top_scorers.head(25).to_csv(outputs / "top_scorers_leaderboard.csv", index=False)
    kpis.to_csv(outputs / "dashboard_kpis.csv", index=False)
    scoring_trend.to_csv(outputs / "world_cup_scoring_trend.csv", index=False)
    points_top_10.to_csv(outputs / "world_cup_points_top_10.csv", index=False)
    dominance_top_10.to_csv(outputs / "team_dominance_top_10.csv", index=False)

    for key in [
        "matches",
        "teams",
        "world_cup_matches",
        "goals",
        "top_elo_team",
        "top_scorer",
    ]:
        row = kpis.iloc[[
            {
                "matches": 0,
                "teams": 1,
                "world_cup_matches": 2,
                "goals": 3,
                "top_elo_team": 4,
                "top_scorer": 5,
            }[key]
        ]]
        row.to_csv(outputs / f"kpi_{key}.csv", index=False)

    print(f"Created {outputs / 'elo_rankings.csv'}")
    print(f"Created {outputs / 'elo_top_10.csv'}")
    print(f"Created {outputs / 'elo_top_25.csv'}")
    print(f"Created {outputs / 'top_scorers_summary.csv'}")
    print(f"Created {outputs / 'top_scorers_top_10.csv'}")
    print(f"Created {outputs / 'top_scorers_leaderboard.csv'}")
    print(f"Created {outputs / 'dashboard_kpis.csv'}")
    print(f"Created {outputs / 'world_cup_scoring_trend.csv'}")
    print(f"Created {outputs / 'world_cup_points_top_10.csv'}")
    print(f"Created {outputs / 'team_dominance_top_10.csv'}")


if __name__ == "__main__":
    build_tableau_dashboard_tables()
