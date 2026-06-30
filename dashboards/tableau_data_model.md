# Tableau Data Model

This file describes how to build the Tableau data model from the generated CSV
outputs in this repository.

## Connection Mode

Use **Extract** mode for smoother dashboard performance. The CSV files are
small enough for Tableau Public/Desktop to handle comfortably.

## Tables to Connect

Connect to these CSV files:

| Tableau table name | Source file | Grain |
|---|---|---|
| Matches | `data/processed/matches_features.csv` | One row per match |
| Team Matches | `data/processed/team_level.csv` | One row per team per match |
| World Cup Matches | `data/processed/world_cup_matches_2002_2022.csv` | One row per World Cup match |
| World Cup Team Matches | `data/processed/world_cup_team_level_2002_2022.csv` | One row per team per World Cup match |
| Team Summary | `outputs/tables/team_summary_all_matches.csv` | One row per team |
| World Cup Team Summary | `outputs/tables/team_summary_world_cup_2002_2022.csv` | One row per team |
| Team Dominance Index | `outputs/tables/team_dominance_index_main.csv` | One row per team |
| TDI Weighting Comparison | `outputs/tables/team_dominance_index_weighting_comparison.csv` | One row per team |
| Team Tournament World Cup | `outputs/tables/team_by_tournament_world_cup.csv` | One row per team per World Cup year |
| World Cup Consistency | `outputs/tables/world_cup_consistency_score.csv` | One row per team |
| Goalscorers | `data/processed/goalscorers_clean.csv` | One row per goal event |

## Relationships

In Tableau's logical data model canvas, create relationships rather than
physical joins where possible:

| Left table | Right table | Relationship fields |
|---|---|---|
| Matches | Team Matches | `match_id = match_id` |
| Team Summary | Team Dominance Index | `team = team` |
| Team Summary | TDI Weighting Comparison | `team = team` |
| Team Summary | World Cup Team Summary | `team = team` |
| Team Summary | World Cup Consistency | `team = team` |
| World Cup Team Summary | Team Tournament World Cup | `team = team` |

For goal-event World Cup filtering, relate or join Goalscorers to World Cup
Matches using all three keys:

- `date`
- `home_team`
- `away_team`

This avoids incorrect matches on dates where multiple games occurred.

## Data Types

Set these key fields:

| Field | Tableau type |
|---|---|
| `date` | Date |
| `match_id` | Number whole |
| `year`, `decade`, `world_cup_year` | Number whole |
| score/count fields | Number whole |
| rate/index fields | Number decimal |
| boolean fields such as `win`, `draw`, `loss`, `is_world_cup` | Boolean |

Leave blank `world_cup_year` values blank for non-World-Cup rows.

## Validation Checks

After connecting, confirm:

| Table | Expected rows |
|---|---:|
| Matches | 49,215 |
| Team Matches | 98,430 |
| World Cup Matches | 384 |
| World Cup Team Matches | 768 |
| Team Tournament World Cup | 192 |

The World Cup page should show six tournament years only:

```text
2002, 2006, 2010, 2014, 2018, 2022
```
