# Tableau Dashboard Build Pack

This folder contains a Tableau-ready dashboard build pack for the World Cup
Analytics project. It includes a packaged starter workbook, a generated Tableau
Hyper extract, and exact implementation guidance for polishing the dashboard on
macOS with Tableau Desktop or Tableau Public.

## Files

| File | Purpose |
|---|---|
| `tableau_data_model.md` | CSV imports, relationships, data types, and refresh checks |
| `tableau_calculated_fields.md` | Ready-to-create Tableau calculated fields |
| `tableau_dashboard_specs.md` | Worksheet and dashboard layout specifications |
| `tableau/world_cup_analytics_dashboard.twbx` | Packaged Tableau starter workbook |
| `tableau/world_cup_analytics_dashboard.twb` | Generated Tableau workbook XML |
| `tableau/world_cup_analytics.hyper` | Tableau extract containing all dashboard tables |

The packaged workbook includes one starter dashboard and five worksheets. Open
it in Tableau Desktop/Public for final layout polish and screenshot validation.

## Source Tables

The easiest path is to open:

```text
dashboards/tableau/world_cup_analytics_dashboard.twbx
```

To build manually or reconnect data, connect Tableau to:

```text
dashboards/tableau/world_cup_analytics.hyper
```

The extract contains these generated tables:

| File | Use |
|---|---|
| `data/processed/matches_features.csv` | Match-level fact table |
| `data/processed/team_level.csv` | Team-perspective fact table, 2 rows per match |
| `data/processed/world_cup_matches_2002_2022.csv` | World Cup final-tournament matches only |
| `data/processed/world_cup_team_level_2002_2022.csv` | World Cup team-perspective rows |
| `outputs/tables/team_summary_all_matches.csv` | All-time team summary |
| `outputs/tables/team_summary_world_cup_2002_2022.csv` | World Cup team summary |
| `outputs/tables/team_dominance_index_main.csv` | Main Team Dominance Index |
| `outputs/tables/team_dominance_index_weighting_comparison.csv` | TDI sensitivity comparison |
| `outputs/tables/team_by_tournament_world_cup.csv` | Team-by-World-Cup-year summary |
| `outputs/tables/world_cup_consistency_score.csv` | World Cup consistency scores |
| `data/processed/goalscorers_clean.csv` | Goal-event table |

## Recommended Dashboard Pages

1. **Executive Overview**: project scale, total matches, teams covered, top
   Dominance Index ranking, match volume trend.
2. **Team Performance**: all-time team comparison using win rate, points per
   match, goal differential, and dominant-win rate.
3. **World Cup 2002-2022**: final-tournament-only rankings and scoring trends.
4. **Team Dominance Index**: composite ranking, components, and sensitivity
   comparison.
5. **Goal Events**: top scorers, penalties, own goals, and goal timing.

## Refresh Workflow

1. Run `python3 src/run_pipeline.py`.
2. Run `python3 scripts/create_tableau_hyper.py` from the repository root.
3. Run `python3 scripts/create_tableau_workbook.py` from the repository root.
4. Open `dashboards/tableau/world_cup_analytics_dashboard.twbx` in Tableau.
5. Confirm row counts:
   - Matches: 49,215
   - Team Matches: 98,430
   - World Cup Matches: 384
   - World Cup Team Matches: 768

## Important Scope Notes

- World Cup analysis must use only `FIFA World Cup` final-tournament rows from
  2002, 2006, 2010, 2014, 2018, and 2022.
- Do not include FIFA World Cup qualification.
- Do not include 2026 scheduled fixtures as results.
- Use minimum-match filters for rate-based all-time rankings.
