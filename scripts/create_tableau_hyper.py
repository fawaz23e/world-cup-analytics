"""Build a Tableau Hyper extract from the cleaned World Cup analytics outputs."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Callable

from tableauhyperapi import (
    Connection,
    CreateMode,
    HyperProcess,
    Inserter,
    Nullability,
    SqlType,
    TableDefinition,
    TableName,
    Telemetry,
)

ROOT = Path(__file__).resolve().parents[1]
TABLEAU_DIR = ROOT / "dashboards" / "tableau"
HYPER_PATH = TABLEAU_DIR / "world_cup_analytics.hyper"


TABLES = {
    "matches": ROOT / "data" / "processed" / "matches_features.csv",
    "team_matches": ROOT / "data" / "processed" / "team_level.csv",
    "world_cup_matches": ROOT / "data" / "processed" / "world_cup_matches_2002_2022.csv",
    "world_cup_team_matches": ROOT / "data" / "processed" / "world_cup_team_level_2002_2022.csv",
    "team_summary": ROOT / "outputs" / "tables" / "team_summary_all_matches.csv",
    "world_cup_team_summary": ROOT
    / "outputs"
    / "tables"
    / "team_summary_world_cup_2002_2022.csv",
    "team_dominance_index": ROOT / "outputs" / "tables" / "team_dominance_index_main.csv",
    "tdi_weighting_comparison": ROOT
    / "outputs"
    / "tables"
    / "team_dominance_index_weighting_comparison.csv",
    "team_tournament_world_cup": ROOT
    / "outputs"
    / "tables"
    / "team_by_tournament_world_cup.csv",
    "world_cup_consistency": ROOT / "outputs" / "tables" / "world_cup_consistency_score.csv",
    "goalscorers": ROOT / "data" / "processed" / "goalscorers_clean.csv",
    "dashboard_kpis": ROOT / "outputs" / "tables" / "dashboard_kpis.csv",
    "kpi_matches": ROOT / "outputs" / "tables" / "kpi_matches.csv",
    "kpi_teams": ROOT / "outputs" / "tables" / "kpi_teams.csv",
    "kpi_world_cup_matches": ROOT / "outputs" / "tables" / "kpi_world_cup_matches.csv",
    "kpi_goals": ROOT / "outputs" / "tables" / "kpi_goals.csv",
    "kpi_top_elo_team": ROOT / "outputs" / "tables" / "kpi_top_elo_team.csv",
    "kpi_top_scorer": ROOT / "outputs" / "tables" / "kpi_top_scorer.csv",
    "elo_rankings": ROOT / "outputs" / "tables" / "elo_rankings.csv",
    "elo_top_10": ROOT / "outputs" / "tables" / "elo_top_10.csv",
    "elo_top_25": ROOT / "outputs" / "tables" / "elo_top_25.csv",
    "top_scorers_summary": ROOT / "outputs" / "tables" / "top_scorers_summary.csv",
    "top_scorers_top_10": ROOT / "outputs" / "tables" / "top_scorers_top_10.csv",
    "top_scorers_leaderboard": ROOT / "outputs" / "tables" / "top_scorers_leaderboard.csv",
    "world_cup_scoring_trend": ROOT / "outputs" / "tables" / "world_cup_scoring_trend.csv",
    "world_cup_points_top_10": ROOT / "outputs" / "tables" / "world_cup_points_top_10.csv",
    "team_dominance_top_10": ROOT / "outputs" / "tables" / "team_dominance_top_10.csv",
}

INT_COLUMNS = {
    "match_id",
    "home_score",
    "away_score",
    "year",
    "decade",
    "total_goals",
    "goal_difference",
    "absolute_goal_difference",
    "world_cup_year",
    "goals_for",
    "goals_against",
    "points",
    "matches_played",
    "matches",
    "wins",
    "draws",
    "losses",
    "goals_scored",
    "goals_conceded",
    "total_goal_differential",
    "dominant_wins",
    "n_tournaments",
    "minute",
    "goal_count",
    "sort_order",
    "elo_rank",
    "scorer_rank",
    "points_rank",
    "dominance_rank",
    "goals",
    "penalties",
    "own_goals",
}

FLOAT_COLUMNS = {
    "win_rate",
    "draw_rate",
    "loss_rate",
    "avg_goal_diff",
    "goals_scored_per_match",
    "goals_conceded_per_match",
    "points_per_match",
    "dominant_win_rate",
    "consistency_score",
    "n_win_rate",
    "n_avg_goal_diff",
    "n_points_per_match",
    "n_dominant_win_rate",
    "n_consistency",
    "dominance_index",
    "mean_ppm",
    "std_ppm",
    "pct_positive_gd",
    "main_rank",
    "equal_weight_rank",
    "performance_heavy_rank",
    "max_rank_shift",
    "kpi_value",
    "elo_rating",
    "avg_goals_per_match",
}

BOOL_COLUMNS = {
    "neutral",
    "is_draw",
    "home_win",
    "away_win",
    "dominant_win",
    "neutral_match",
    "is_world_cup",
    "win",
    "draw",
    "loss",
    "own_goal",
    "penalty",
    "minute_missing",
    "scorer_missing",
}

DATE_COLUMNS = {"date", "last_match_date", "first_goal_date", "latest_goal_date"}


def normalize_column_name(name: str) -> str:
    return name.strip().replace(" ", "_").replace("-", "_").lower()


def column_type(name: str) -> SqlType:
    if name in DATE_COLUMNS:
        return SqlType.date()
    if name in BOOL_COLUMNS:
        return SqlType.bool()
    if name in INT_COLUMNS:
        return SqlType.big_int()
    if name in FLOAT_COLUMNS:
        return SqlType.double()
    return SqlType.text()


def converter(name: str) -> Callable[[str], object]:
    if name in DATE_COLUMNS:
        return lambda value: date.fromisoformat(value) if value else None
    if name in BOOL_COLUMNS:
        return lambda value: (
            None if value == "" else value.strip().lower() in {"true", "1", "yes"}
        )
    if name in INT_COLUMNS:
        return lambda value: None if value == "" else int(float(value))
    if name in FLOAT_COLUMNS:
        return lambda value: None if value == "" else float(value)
    return lambda value: None if value == "" else value


def read_csv_rows(csv_path: Path, table_name: str) -> tuple[list[str], list[list[object]]]:
    with csv_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError(f"{csv_path} does not contain a header row")

        columns = [normalize_column_name(name) for name in reader.fieldnames]
        if table_name == "goalscorers":
            columns.append("goal_count")

        converters = [converter(column) for column in columns]
        rows = []
        for row in reader:
            values = [row[original_name].strip() for original_name in reader.fieldnames]
            if table_name == "goalscorers":
                values.append("1")
            rows.append([convert(value) for value, convert in zip(values, converters)])

    return columns, rows


def create_table(connection: Connection, table_name: str, csv_path: Path) -> int:
    columns, rows = read_csv_rows(csv_path, table_name)
    definition = TableDefinition(
        TableName("Extract", table_name),
        [
            TableDefinition.Column(column, column_type(column), Nullability.NULLABLE)
            for column in columns
        ],
    )

    connection.catalog.create_table(definition)
    with Inserter(connection, definition) as inserter:
        inserter.add_rows(rows)
        inserter.execute()

    return len(rows)


def main() -> None:
    TABLEAU_DIR.mkdir(parents=True, exist_ok=True)
    try:
        from create_tableau_dashboard_tables import build_tableau_dashboard_tables
    except ModuleNotFoundError as exc:
        if exc.name != "pandas":
            raise
        print("Skipping dashboard table rebuild because pandas is not installed in this environment.")
    else:
        build_tableau_dashboard_tables(ROOT)

    if HYPER_PATH.exists():
        HYPER_PATH.unlink()

    with HyperProcess(
        telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU,
        user_agent="world-cup-analytics",
    ) as hyper:
        with Connection(
            endpoint=hyper.endpoint,
            database=HYPER_PATH,
            create_mode=CreateMode.CREATE_AND_REPLACE,
        ) as connection:
            connection.catalog.create_schema("Extract")
            for table_name, csv_path in TABLES.items():
                count = create_table(connection, table_name, csv_path)
                print(f"{table_name}: {count:,} rows")

    print(f"Created {HYPER_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
