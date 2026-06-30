# Project Summary: FIFA World Cup & International Football Analytics

## Objective

Identify and evaluate the strongest national football teams historically and
at FIFA World Cup final tournaments from 2002 onward, using a reproducible
Python data pipeline, with statistical rigor and an explicit accounting of
the resulting ranking's limitations.

## Dataset

Four CSVs: `results.csv` (49,287 rows, 1872-2026), `goalscorers.csv` (47,601
goal events), `shootouts.csv` (675 penalty shootouts), `former_names.csv` (36
historical name changes). The raw match file spans 1872-11-30 to scheduled
fixtures on 2026-06-27; after cleaning, 49,215 played matches remain, ending on
2026-03-31 (72 unplayed/scheduled 2026 World Cup fixtures removed). 333
distinct team names and 193 distinct tournament names appear in the raw data.

## Methods

1. **Cleaning** (`src/data_cleaning.py`): date parsing, duplicate detection
   (0 exact duplicates; 2 legitimate same-day fixtures flagged, not dropped),
   missing-score handling (all 72 nulls were unplayed 2026 fixtures, dropped),
   boolean standardization, validation contract (no negative scores, all
   teams/dates present, every match has a determinate outcome).
2. **Feature engineering** (`src/feature_engineering.py`): match-level derived
   columns (goal difference, dominant win at >=3 goals, World Cup flags,
   tournament category) and a team-level exploded table (one row per team per
   match), reconciled against the match-level table.
3. **World Cup filtering**: isolating the literal tournament name `FIFA World
   Cup` for `year >= 2002`, excluding 2026 (0 played matches) -- verified to
   yield exactly the six expected tournaments (2002-2022) at 64 matches each.
4. **Team metrics** (`src/metrics.py`): win/draw/loss rate, goal differential,
   points per match, dominant-win rate -- computed for all matches, World Cup
   matches since 2002, and team-by-tournament grain.
5. **Team Dominance Index**: a weighted, min-max-normalized composite of win
   rate (25%), average goal differential (25%), points per match (20%),
   dominant-win rate (15%), and a World Cup Consistency Score (15%), restricted
   to teams with >= 300 career matches.
6. **Statistical analysis**: Pearson correlations between metrics, a one-way
   ANOVA on World Cup scoring across tournaments, and a chi-square test of
   home-field advantage.
7. **Visualization**: 12 Matplotlib charts saved at 300 DPI to `outputs/figures/`.
8. **SQL validation**: PostgreSQL schema and analysis queries executed
   successfully against local PostgreSQL 16, loading 49,215 match rows and
   98,430 team-match rows.

## Cleaning decisions worth discussing

- Missing scores were never imputed; they were entirely 2026 World Cup
  fixtures that have not been played, so they were dropped from match-level
  analysis with that reasoning made explicit.
- Historical team-name standardization (`former_names.csv`) was deliberately
  **not** auto-applied -- merging e.g. Czechoslovakia into Czech Republic would
  conflate different squads, eras, and political entities. The mapping table
  is preserved as documentation, not enforced.
- A 300-match minimum threshold was chosen for rate-based main rankings after
  observing that, below it, non-FIFA/regional associations (Jersey, Guernsey,
  Basque Country) dominate win-rate leaderboards due to weak competition pools.

## Metrics

See `outputs/tables/` for every computed table: `team_summary_all_matches.csv`,
`team_summary_world_cup_2002_2022.csv`, `team_by_tournament_world_cup.csv`,
`world_cup_consistency_score.csv`, and the three Dominance Index weighting
variants plus their comparison and sensitivity tables.

## Main findings

- Brazil tops the all-time Team Dominance Index (100.0/100, min. 300 matches),
  ahead of Spain (91.5), Germany (90.5), England (89.5), Netherlands (86.1) --
  stable across three different weighting schemes.
- Brazil and Germany lead World Cup points since 2002 (74 and 73 from 34
  matches each, both at a 67.6% win rate).
- The Netherlands has the best overall World Cup points-per-match (2.30)
  among teams with 3+ tournament appearances.
- World Cup scoring rate (2.27-2.69 goals/match, 2002-2022) shows no
  statistically significant trend (ANOVA F=0.84, p=0.52).
- Home teams win significantly more often at non-neutral venues (50.7%) than
  on neutral grounds (44.1%), chi-square p < 0.001, across the full 1872-2026
  dataset.
- Win rate and average goal differential are highly correlated (r=0.97) among
  high-sample teams, indicating substantial metric redundancy.

## Statistical results

| Test | Statistic | Result |
|---|---|---|
| win_rate vs. avg_goal_diff (Pearson) | r=0.972, p=9.5e-85 | Strong positive correlation |
| dominant_win_rate vs. points_per_match (Pearson) | r=0.859, p=7.8e-40 | Strong positive correlation |
| Goals/match across 6 World Cups (ANOVA) | F=0.841, p=0.521 | No significant difference |
| Neutral vs. non-neutral home-win rate (Chi-square) | chi2=165.3, p=7.8e-38 | Significant difference |

## Limitations

No opponent-strength adjustment; historical team identities kept separate
rather than merged; rate-based rankings sensitive to the minimum-match
threshold; Dominance Index weights are analyst-defined; a Tableau packaged
starter workbook, Hyper extract, and build pack with data model, calculated
fields, and dashboard specs are included.

## Conclusion

The cleaned, validated dataset supports a defensible, transparent ranking of
international football teams and a focused look at World Cup performance
since 2002. Brazil and Germany emerge as the most successful teams across
both the all-time and World Cup-specific analyses, a result that is robust to
reasonable changes in metric weighting but sensitive to sample-size
thresholds -- a finding documented and quantified, not hidden, in
`notebooks/04_team_dominance_index.ipynb`.
