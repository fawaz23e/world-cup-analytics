# Tableau Dashboard Specifications

Build these worksheets and assemble them into a Tableau story or dashboard set.

## Dashboard 1: Executive Overview

Purpose: summarize project scale and top teams.

Worksheets:

| Worksheet | Source | Marks / fields |
|---|---|---|
| KPI: Matches | Matches | Text: `COUNTD(match_id)` |
| KPI: Teams | Team Matches | Text: `COUNTD(team)` |
| KPI: World Cup Matches | World Cup Matches | Text: `COUNTD(match_id)` |
| Top Dominance Index | Team Dominance Index | Rows: `team`; Columns: `dominance_index`; Top 10 filter |
| Matches by Year | Matches | Columns: `year`; Rows: count of matches |
| Goals per Match by Year | Matches | Columns: `year`; Rows: average `total_goals` |

Recommended filters:

- Year range.
- Tournament category.

## Dashboard 2: Team Performance

Purpose: compare all-time international performance.

Worksheets:

| Worksheet | Source | Marks / fields |
|---|---|---|
| Team Summary Table | Team Summary | `team`, `matches_played`, `wins`, `win_rate`, `avg_goal_diff`, `points_per_match`, `dominant_win_rate` |
| Top Wins | Team Summary | Bar chart by `wins`, top 15 |
| Win Rate | Team Summary | Bar chart by `win_rate`, filter `matches_played >= 300` |
| Attack vs Defense | Team Summary | Scatter: `goals_conceded_per_match` vs `goals_scored_per_match`; detail `team`; size `matches_played` |
| Dominant Wins | Team Summary | Bar chart by `dominant_wins`, top 15 |

Default filter:

```text
matches_played >= 300
```

This avoids small-sample rankings being dominated by regional/non-FIFA teams.

## Dashboard 3: World Cup 2002-2022

Purpose: isolate FIFA men's World Cup final-tournament performance.

Worksheets:

| Worksheet | Source | Marks / fields |
|---|---|---|
| World Cup Points | World Cup Team Summary | Bar chart by `points`, top 15 |
| World Cup Win Rate | World Cup Team Summary | Bar chart by `win_rate`, minimum 10 matches recommended |
| Team-Year Heatmap | Team Tournament World Cup | Rows: `team`; Columns: `world_cup_year`; Color/Text: `points` |
| Scoring Trends | World Cup Matches | Columns: `world_cup_year`; Rows: average `total_goals` |
| Tournament Counts | World Cup Matches | Columns: `world_cup_year`; Rows: count distinct `match_id` |

Validation:

- Each World Cup year should show 64 matches.
- Years should be 2002, 2006, 2010, 2014, 2018, 2022 only.

## Dashboard 4: Team Dominance Index

Purpose: explain and compare the composite ranking.

Worksheets:

| Worksheet | Source | Marks / fields |
|---|---|---|
| TDI Ranking | Team Dominance Index | Bar chart by `dominance_index`, top 15 |
| TDI Components | Team Dominance Index | Table: `win_rate`, `avg_goal_diff`, `points_per_match`, `dominant_win_rate`, `consistency_score` |
| Consistency vs Performance | Team Dominance Index | Scatter: `points_per_match` vs `consistency_score`; size/color `dominance_index` |
| Weighting Comparison | TDI Weighting Comparison | Table: `main_rank`, `equal_weight_rank`, `performance_heavy_rank`, `max_rank_shift` |

Text box:

```text
Team Dominance Index = 25% win rate + 25% average goal differential
+ 20% points per match + 15% dominant-win rate + 15% World Cup consistency.
```

## Dashboard 5: Goal Events

Purpose: show player/scorer-level context.

Worksheets:

| Worksheet | Source | Marks / fields |
|---|---|---|
| Top Scorers | Goalscorers | Rows: `scorer`; Columns: count goals; top 20 |
| Goals by Team | Goalscorers | Rows: `team`; Columns: count goals |
| Goal Minute Distribution | Goalscorers | Columns: `Goal Minute Bin`; Rows: count goals |
| Penalty and Own Goal KPIs | Goalscorers | Text cards from calculated fields |

Optional:

- Create a World Cup Goalscorers source by joining Goalscorers to World Cup
  Matches on `date`, `home_team`, and `away_team`.

## Publishing Notes

- If using Tableau Public, avoid publishing private/local paths in screenshots.
- Do not claim a packaged Tableau workbook exists unless a `.twb` or `.twbx`
  is actually created in Tableau Desktop/Public.
- Include dashboard screenshots in GitHub only after visually checking them.
