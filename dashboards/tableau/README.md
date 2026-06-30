# Tableau Extract

`world_cup_analytics_dashboard.twbx` is the packaged Tableau starter workbook.
Open it in Tableau Desktop or Tableau Public, then polish the layout and
validate screenshots before publishing.

`world_cup_analytics.hyper` is the Tableau-ready extract used by the workbook.

To recreate the extract after changing the pipeline:

```bash
python3 scripts/create_tableau_hyper.py
python3 scripts/create_tableau_workbook.py
```

Expected tables:

| Table | Rows |
|---|---:|
| `matches` | 49,215 |
| `team_matches` | 98,430 |
| `world_cup_matches` | 384 |
| `world_cup_team_matches` | 768 |
| `team_summary` | 333 |
| `world_cup_team_summary` | 61 |
| `team_dominance_index` | 133 |
| `tdi_weighting_comparison` | 133 |
| `team_tournament_world_cup` | 192 |
| `world_cup_consistency` | 42 |
| `goalscorers` | 47,601 |
