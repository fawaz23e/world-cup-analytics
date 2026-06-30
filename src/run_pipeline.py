"""
run_pipeline.py
---------------
End-to-end driver: clean -> engineer features -> compute metrics ->
save every table required by the project spec under outputs/tables/
and data/processed/. Run with:  python3 src/run_pipeline.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from data_cleaning import run_cleaning_pipeline, find_conflicting_duplicates
from feature_engineering import (
    add_match_features,
    build_team_level,
    validate_team_level,
    filter_world_cup_since_2002,
)
from metrics import (
    team_summary,
    world_cup_tournament_summary,
    consistency_score,
    team_dominance_index,
    DEFAULT_WEIGHTS,
    EQUAL_WEIGHTS,
    PERFORMANCE_HEAVY_WEIGHTS,
)
from visualization import generate_all

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Below this many career matches, win/loss rate metrics are dominated by
# small samples and (in this dataset) by sub-national / non-FIFA regional
# associations (Jersey, Guernsey, Padania, Basque Country, etc.) that play
# almost exclusively against similarly small opponents. 300 matches is
# roughly the point where these entities drop out of the table.
MAIN_MIN_MATCHES = 300


def main() -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("== Cleaning ==")
    cleaned = run_cleaning_pipeline()
    print({k: v.shape for k, v in cleaned.items()})
    print("Cleaning log:", cleaned["results"].attrs.get("cleaning_log"))

    conflicts = find_conflicting_duplicates(cleaned["results"])
    print(f"Conflicting (non-exact) duplicate date/home/away rows: {len(conflicts)}")
    conflicts.to_csv(TABLES_DIR / "conflicting_duplicate_matches.csv", index=False)

    print("== Feature engineering ==")
    matches = add_match_features(cleaned["results"])
    teams = build_team_level(matches)
    checks = validate_team_level(matches, teams)
    print("Team-level validation:", checks)

    matches.to_csv(PROCESSED_DIR / "matches_features.csv", index=False)
    teams.to_csv(PROCESSED_DIR / "team_level.csv", index=False)

    wc_matches = filter_world_cup_since_2002(matches)
    wc_teams = build_team_level(wc_matches)
    wc_matches.to_csv(PROCESSED_DIR / "world_cup_matches_2002_2022.csv", index=False)
    wc_teams.to_csv(PROCESSED_DIR / "world_cup_team_level_2002_2022.csv", index=False)
    print("World Cup years present:", sorted(wc_matches["year"].dropna().unique()))

    print("== Team metrics ==")
    all_time_summary = team_summary(teams, min_matches=1)
    all_time_summary.to_csv(TABLES_DIR / "team_summary_all_matches.csv", index=False)

    wc_summary = team_summary(wc_teams, min_matches=1)
    wc_summary.to_csv(TABLES_DIR / "team_summary_world_cup_2002_2022.csv", index=False)

    wc_tournament = world_cup_tournament_summary(wc_teams)
    wc_tournament.to_csv(TABLES_DIR / "team_by_tournament_world_cup.csv", index=False)

    print("== Consistency score ==")
    consistency = consistency_score(wc_tournament, min_tournaments=2)
    consistency.to_csv(TABLES_DIR / "world_cup_consistency_score.csv", index=False)

    print("== Team Dominance Index ==")
    tdi_main = team_dominance_index(
        all_time_summary, consistency, weights=DEFAULT_WEIGHTS,
        min_matches=MAIN_MIN_MATCHES, normalization="minmax",
    )
    tdi_main.to_csv(TABLES_DIR / "team_dominance_index_main.csv", index=False)

    tdi_equal = team_dominance_index(
        all_time_summary, consistency, weights=EQUAL_WEIGHTS,
        min_matches=MAIN_MIN_MATCHES, normalization="minmax",
    )
    tdi_equal.to_csv(TABLES_DIR / "team_dominance_index_equal_weight.csv", index=False)

    tdi_perf = team_dominance_index(
        all_time_summary, consistency, weights=PERFORMANCE_HEAVY_WEIGHTS,
        min_matches=MAIN_MIN_MATCHES, normalization="minmax",
    )
    tdi_perf.to_csv(TABLES_DIR / "team_dominance_index_performance_heavy.csv", index=False)

    # Ranking comparison across the three weighting schemes.
    cmp_df = tdi_main[["team", "dominance_index"]].rename(columns={"dominance_index": "main"})
    cmp_df["main_rank"] = cmp_df["main"].rank(ascending=False).astype(int)
    eq = tdi_equal[["team", "dominance_index"]].rename(columns={"dominance_index": "equal_weight"})
    eq["equal_weight_rank"] = eq["equal_weight"].rank(ascending=False).astype(int)
    pf = tdi_perf[["team", "dominance_index"]].rename(columns={"dominance_index": "performance_heavy"})
    pf["performance_heavy_rank"] = pf["performance_heavy"].rank(ascending=False).astype(int)
    cmp_df = cmp_df.merge(eq, on="team").merge(pf, on="team")
    cmp_df["max_rank_shift"] = (
        cmp_df[["main_rank", "equal_weight_rank", "performance_heavy_rank"]].max(axis=1)
        - cmp_df[["main_rank", "equal_weight_rank", "performance_heavy_rank"]].min(axis=1)
    )
    cmp_df = cmp_df.sort_values("main_rank")
    cmp_df.to_csv(TABLES_DIR / "team_dominance_index_weighting_comparison.csv", index=False)

    # Minimum-match sensitivity analysis.
    sens_rows = []
    for thresh in [50, 100, 150, 200, 300, 400]:
        tdi_t = team_dominance_index(all_time_summary, consistency, weights=DEFAULT_WEIGHTS,
                                      min_matches=thresh, normalization="minmax")
        top5 = tdi_t.head(5)["team"].tolist()
        sens_rows.append({"min_matches_threshold": thresh, "n_teams": len(tdi_t), "top_5_teams": ", ".join(top5)})
    pd.DataFrame(sens_rows).to_csv(TABLES_DIR / "min_matches_sensitivity.csv", index=False)

    # Dominant-win margin sensitivity (2 / 3 / 4 goals).
    margin_rows = []
    for margin in [2, 3, 4]:
        m2 = add_match_features(cleaned["results"], dominant_margin=margin)
        t2 = build_team_level(m2)
        # build_team_level recomputes dominant_win with hardcoded margin 3;
        # recompute explicitly here for the sensitivity test.
        t2["dominant_win"] = t2["win"] & (t2["goal_difference"].abs() >= margin)
        s2 = team_summary(t2, min_matches=MAIN_MIN_MATCHES)
        top_dominant = s2.sort_values("dominant_win_rate", ascending=False).head(5)["team"].tolist()
        margin_rows.append({
            "dominant_margin": margin,
            "league_wide_dominant_win_rate": round(t2["dominant_win"].sum() / t2["win"].sum(), 4),
            "top_5_by_dominant_win_rate": ", ".join(top_dominant),
        })
    pd.DataFrame(margin_rows).to_csv(TABLES_DIR / "dominant_margin_sensitivity.csv", index=False)

    print("== Visualizations ==")
    generate_all(matches, all_time_summary, wc_summary, wc_matches, wc_tournament, tdi_main)

    print("\nAll tables written to: outputs/tables")
    print("All figures written to: outputs/figures")
    print("Done.")


if __name__ == "__main__":
    main()
