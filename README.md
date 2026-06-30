# FIFA World Cup & International Football Analytics

A reproducible Python data analytics project analyzing 49,000+ international
football matches (1872-2026) to identify the strongest national teams in
history and at FIFA World Cup final tournaments from 2002 onward.

## Project overview

This project cleans, engineers, and analyzes historical international
football results to answer questions about long-term team dominance and
World Cup-specific performance, using pandas, basic statistics, and a
transparent custom ranking (the Team Dominance Index). A modest, genuinely
executable SQL component and a documented Tableau build pack are included to
reflect the original tech stack, but the project's substance is the Python
analysis in `notebooks/` and `src/`.

**Scope note:** although the original dataset and project name reference the
upcoming 2026 World Cup, this project's analysis covers FIFA World Cup final
tournaments **2002-2022 only**. The 2026 fixtures present in the raw data are
scheduled matches with no recorded score and are excluded from every table,
chart, and metric in this repository -- no 2026 result is fabricated or
estimated anywhere in this project.

## Analytical questions

1. Which national teams have been the strongest in international football, all-time?
2. Which teams have been strongest at FIFA World Cup final tournaments since 2002?
3. Which teams have produced the most dominant wins?
4. Which teams have shown the greatest consistency across World Cup tournaments?
5. How have scoring patterns changed across World Cups, 2002-2022?
6. How do win rate, goal differential, points per match, and dominant-win rate
   interact to drive a composite team ranking, and how sensitive is that
   ranking to the weights and sample-size thresholds chosen?

## Datasets

| File | Rows (cleaned) | Description |
|---|---|---|
| `data/raw/results.csv` | 49,287 raw / 49,215 played | Match-level results, 1872-2026 |
| `data/raw/goalscorers.csv` | 47,601 | Goal-event log: scorer, minute, own goal, penalty |
| `data/raw/shootouts.csv` | 675 | Penalty shootout winners |
| `data/raw/former_names.csv` | 36 | Historical national-team name changes (reference only) |

**Source:** publicly available historical international football results
(originally compiled from Kaggle football-results datasets). **Date range:**
1872-11-30 to 2026-06-27 in the raw file; the last played match is
2026-03-31. The 72 later rows are unplayed/scheduled 2026 World Cup
fixtures, dropped during cleaning.
**Coverage:** 333 distinct team names (including non-FIFA regional/
sub-national associations -- see Limitations), 193 distinct tournament names.

## Technologies

- **Python** -- pandas, NumPy, SciPy, Matplotlib (core analysis)
- **Jupyter Notebook** -- four sequential analysis notebooks
- **SQL / PostgreSQL** -- a parallel, genuinely executable query layer (see SQL section)
- **Tableau** -- packaged starter workbook, generated Hyper extract, data model, and calculated fields (see Tableau section)
- **Git / GitHub** -- version control

## Repository structure

```
world-cup-analytics/
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
├── data/
│   ├── raw/                  # original, unmodified source CSVs
│   └── processed/            # cleaned + feature-engineered outputs
├── notebooks/
│   ├── 01_data_audit_and_cleaning.ipynb
│   ├── 02_exploratory_analysis.ipynb
│   ├── 03_world_cup_analysis.ipynb
│   └── 04_team_dominance_index.ipynb
├── src/
│   ├── data_cleaning.py
│   ├── feature_engineering.py
│   ├── metrics.py
│   ├── visualization.py
│   └── run_pipeline.py        # end-to-end driver script
├── outputs/
│   ├── figures/               # 12 saved charts (PNG, 300 DPI)
│   └── tables/                # every metrics/ranking table as CSV
├── sql/
│   ├── schema.sql
│   └── analysis_queries.sql
├── reports/
│   └── project_summary.md
└── dashboards/
    ├── README.md                  # Tableau workbook/build pack overview
    ├── tableau_data_model.md      # import tables, relationships, refresh checks
    ├── tableau_calculated_fields.md
    └── tableau_dashboard_specs.md # dashboard page and visual specs
```

## Cleaning methodology

Implemented in `src/data_cleaning.py`, run via `run_cleaning_pipeline()`:

- Loads all four raw files with `pathlib`, never modifying them in place.
- Parses `date` to a real datetime; 0 rows had unparseable dates.
- Drops 72 rows with missing scores -- confirmed to be exclusively 2026 FIFA
  World Cup fixtures with no recorded outcome (i.e., not yet played).
- Removes exact duplicate rows (0 found).
- Flags, but does not auto-drop, rows that share (date, home_team, away_team)
  but differ elsewhere -- 2 such rows exist (two genuinely different
  Tahiti vs. New Caledonia matches played the same day in 1974) and are kept.
- Validates: no negative scores, home/away teams always present, all dates
  valid, every remaining match has a determinate score.
- Standardizes the `neutral` column to boolean.
- `former_names.csv` is cleaned and retained as a **documented reference
  table only** -- it is intentionally not used to auto-merge historical teams
  into their modern successors (see "Limitations").
- Writes cleaned files to `data/processed/`.

## Feature engineering

Implemented in `src/feature_engineering.py`:

- Match-level: `year`, `decade`, `total_goals`, `goal_difference`,
  `absolute_goal_difference`, `match_result`, `winner`, `loser`, `is_draw`,
  `home_win`, `away_win`, `dominant_win` (margin >= 3 goals, the project
  default -- see sensitivity analysis in notebook 04), `neutral_match`,
  `is_world_cup`, `world_cup_year`, `tournament_category`, and a reproducible
  `match_id` for validation and SQL/Tableau joins.
- Team-level: every match is exploded into exactly two rows (one per team) with
  `goals_for`, `goals_against`, `goal_difference`, `result`, `win`/`draw`/`loss`,
  `points` (3/1/0), `dominant_win`. Reconciliation checks confirm 2 team rows
  per match, mutually-exclusive win/draw/loss flags, and goals-for totals
  matching goals-against totals in aggregate.

## World Cup filtering logic

Only the literal tournament name `FIFA World Cup` is treated as the men's
final tournament. The raw data contains exactly three tournament names
containing the phrase "World Cup": `FIFA World Cup` (1,036 matches, 1930-2026),
`FIFA World Cup qualification` (8,771 matches), and `Viva World Cup` (60
matches, an unofficial competition for non-FIFA-affiliated teams) -- the
latter two are excluded. Filtering to `year >= 2002` and explicitly excluding
2026 (which has 0 played matches in this dataset) yields exactly 384 matches
across the 6 expected tournaments: 2002, 2006, 2010, 2014, 2018, 2022 (64
matches each).

## Team metrics

`src/metrics.py::team_summary()` computes, per team: matches played, wins,
draws, losses, win/draw/loss rate, goals scored/conceded (total and per
match), total and average goal differential, points and points per match,
dominant wins, and dominant-win rate -- produced separately for (1) all
international matches, (2) World Cup matches since 2002, and (3)
team-by-tournament World Cup grain.

**Sample-size note:** rate-based rankings (win rate, dominant-win rate) are
reported with a minimum-match threshold of **300 career matches**. Below that
threshold, the leaderboard is dominated by entities such as Jersey, Guernsey,
and the Basque Country -- regional/sub-national associations that are not
full FIFA members and play primarily in minor regional tournaments against
similarly small opposition (see notebook 04 for the full sensitivity table).

## Team Dominance Index

A transparent, analyst-defined composite (`src/metrics.py::team_dominance_index`):

```
dominance_index = 0.25 * norm(win_rate)
                 + 0.25 * norm(avg_goal_diff)
                 + 0.20 * norm(points_per_match)
                 + 0.15 * norm(dominant_win_rate)
                 + 0.15 * norm(world_cup_consistency_score)
```

Normalized via min-max scaling (chosen over z-scores for bounded,
at-a-glance interpretability), re-scaled to 0-100, computed for teams with
>= 300 career matches. Two alternative weightings (equal-weight,
performance-heavy) and a minimum-match / dominant-margin sensitivity analysis
are run in `notebooks/04_team_dominance_index.ipynb` and saved to
`outputs/tables/`.

**World Cup Consistency Score** (`src/metrics.py::consistency_score`):
combines normalized mean points-per-match across World Cup appearances (50%),
share of tournaments with a positive goal differential (30%), and (negatively)
normalized variance in points-per-match (20%), scaled down for teams with
fewer than 3 tournament appearances, computed only for teams with >= 2 World
Cup appearances.

## Main findings (generated by the notebooks in this repository)

- **All-time, min. 300 matches:** Brazil leads the Team Dominance Index
  (100.0/100), followed by Spain (91.5), Germany (90.5), England (89.5), and
  the Netherlands (86.1). This top group is stable across all three tested
  weighting schemes.
- **World Cup points, 2002-2022:** Brazil (74 points, 34 matches) and Germany
  (73 points, 34 matches) lead, both with a 67.6% win rate across that span.
- **World Cup consistency:** the Netherlands has the best overall
  points-per-match of any team with 3+ World Cup appearances (2.30 across 23
  matches in 4 tournaments).
- **Scoring trend:** average World Cup goals-per-match ranged 2.27-2.69 across
  2002-2022 with no statistically significant trend (one-way ANOVA, F=0.84,
  p=0.52).
- **Home-field advantage:** home teams won 50.7% of non-neutral matches vs.
  44.1% on neutral grounds, a statistically significant difference (chi-square
  p < 0.001) across the full 1872-2026 dataset.
- **Top World Cup scorers, 2002-2022:** Miroslav Klose (16), Lionel Messi (13),
  Kylian Mbappé (12).
- **Metric redundancy:** win rate and average goal differential correlate at
  r=0.97 among high-sample teams -- they largely capture the same underlying
  signal rather than independent information.

## Selected charts

All 12 charts are in `outputs/figures/`, including: matches per year (1872-2026),
top teams by win rate, the Team Dominance Index top 15, World Cup team
performance 2002-2022, World Cup scoring trends by tournament, and a
team-by-tournament points heatmap.

## Reproducing the analysis

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the full pipeline (cleaning -> features -> metrics -> tables -> figures):
python3 src/run_pipeline.py

# Or step through the notebooks in order:
jupyter notebook notebooks/01_data_audit_and_cleaning.ipynb
# ... 02, 03, 04
```

All file paths in `src/` are relative to the repository root via `pathlib`,
so the project runs unmodified on any machine.

## SQL instructions

`sql/schema.sql` and `sql/analysis_queries.sql` were executed successfully
against local PostgreSQL 16 on 2026-06-23. The schema loaded
`data/processed/matches_features.csv` (49,215 rows) and
`data/processed/team_level.csv` (98,430 rows), then returned non-empty results
for the analysis queries. To reproduce:

```bash
createdb worldcup
psql worldcup -f sql/schema.sql
psql worldcup -c "\copy matches FROM 'data/processed/matches_features.csv' CSV HEADER"
psql worldcup -c "\copy team_matches FROM 'data/processed/team_level.csv' CSV HEADER"
psql worldcup -f sql/analysis_queries.sql
```
(Column order in the CSVs matches the table definitions; adjust the `\copy`
column list if you've modified `src/feature_engineering.py`.)

## Tableau guidance

The project includes a packaged Tableau workbook at
`dashboards/tableau/world_cup_analytics_dashboard.twbx` and a Tableau-ready
Hyper extract at `dashboards/tableau/world_cup_analytics.hyper`. The packaged
workbook contains a starter dashboard with five worksheets: Team Dominance
Index ranking, World Cup points, scoring trend, team-year points heatmap, and
top scorers.

The workbook is generated from `scripts/create_tableau_workbook.py`; use Tableau
Desktop/Public for final visual polish and screenshots before publishing.

## Limitations

- **No opponent-strength adjustment.** Win rate, goal differential, and the
  Dominance Index are computed against each team's actual schedule, not
  adjusted for the strength of competition the way an Elo system would.
- **Historical team identities are kept separate** from modern successors
  (e.g., Czechoslovakia vs. Czech Republic) rather than merged -- a deliberate
  choice to avoid conflating different squads, eras, and political entities.
  `data/raw/former_names.csv` documents the mappings without applying them.
- **Sample-size sensitivity.** Rate-based rankings shift meaningfully below a
  300-match threshold, where regional/non-FIFA entities enter the leaderboard.
- **The Dominance Index weights are analyst-defined**, not empirically fit to
  an external outcome; alternative weightings are provided for comparison, and
  the top-6 ranking is stable across all three.
- **Tableau workbook is a generated starter dashboard.** Use Tableau Desktop/Public
  for final visual polish and screenshot verification before publishing.

## Future improvements

- Real-time data refresh via a football API.
- An opponent-strength-adjusted (Elo-style) rating to complement the Dominance Index.
- Additional Tableau pages for deeper player-level and tournament-level analysis.
- Extending the World Cup analysis to 2026 once that tournament has been played.

## Author

**Fawaz Elahi**
Bachelor of Science in Applied Statistics and Economics, University of Toronto
GitHub: [github.com/fawaz23e](https://github.com/fawaz23e)
LinkedIn: [linkedin.com/in/fawaz-elahi](https://linkedin.com/in/fawaz-elahi)
