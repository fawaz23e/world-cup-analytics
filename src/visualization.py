"""
visualization.py
-----------------
Matplotlib chart builders for the World Cup Analytics project. Every
function returns a (fig, ax) pair and saves a high-resolution PNG to
outputs/figures/. Charts share a consistent, readable style.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".matplotlib_cache"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

SOURCE_NOTE = "Source: International football results, 1872-2026 (results.csv) | github.com/fawaz23e/world-cup-analytics"


def _save(fig, name: str):
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / name, bbox_inches="tight")
    plt.close(fig)


def chart_matches_by_year(matches: pd.DataFrame):
    yearly = matches.groupby("year").size()
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(yearly.index, yearly.values, color="#1f4e8c", linewidth=1.5)
    ax.set_title("Number of International Matches Played per Year (1872-2026)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Matches played")
    ax.figure.text(0.01, -0.02, SOURCE_NOTE, fontsize=7, color="gray")
    _save(fig, "01_matches_by_year.png")


def chart_avg_goals_over_time(matches: pd.DataFrame):
    yearly = matches.groupby("year")["total_goals"].mean()
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(yearly.index, yearly.values, color="#c0392b", linewidth=1.5)
    ax.set_title("Average Goals per Match Over Time")
    ax.set_xlabel("Year")
    ax.set_ylabel("Average total goals per match")
    _save(fig, "02_avg_goals_over_time.png")


def chart_top_teams_by_wins(summary: pd.DataFrame, n: int = 15):
    top = summary.sort_values("wins", ascending=False).head(n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(top["team"], top["wins"], color="#1f4e8c")
    ax.set_title(f"Top {n} National Teams by Total Wins (All International Matches)")
    ax.set_xlabel("Total wins")
    _save(fig, "03_top_teams_by_wins.png")


def chart_top_teams_by_win_rate(summary: pd.DataFrame, min_matches: int = 300, n: int = 15):
    sub = summary[summary["matches_played"] >= min_matches]
    top = sub.sort_values("win_rate", ascending=False).head(n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(top["team"], top["win_rate"] * 100, color="#2e8b57")
    ax.set_title(f"Top {n} Teams by Win Rate (min. {min_matches} career matches)")
    ax.set_xlabel("Win rate (%)")
    _save(fig, "04_top_teams_by_win_rate.png")


def chart_top_teams_by_goal_diff(summary: pd.DataFrame, min_matches: int = 300, n: int = 15):
    sub = summary[summary["matches_played"] >= min_matches]
    top = sub.sort_values("avg_goal_diff", ascending=False).head(n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(top["team"], top["avg_goal_diff"], color="#8e44ad")
    ax.set_title(f"Top {n} Teams by Average Goal Differential (min. {min_matches} matches)")
    ax.set_xlabel("Average goal differential per match")
    _save(fig, "05_top_teams_by_goal_diff.png")


def chart_most_dominant_wins(summary: pd.DataFrame, min_matches: int = 300, n: int = 15):
    sub = summary[summary["matches_played"] >= min_matches]
    top = sub.sort_values("dominant_wins", ascending=False).head(n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(top["team"], top["dominant_wins"], color="#d35400")
    ax.set_title(f"Teams with the Most Dominant Wins (margin >= 3 goals, min. {min_matches} matches)")
    ax.set_xlabel("Number of dominant wins")
    _save(fig, "06_most_dominant_wins.png")


def chart_wc_team_performance(wc_summary: pd.DataFrame, n: int = 15):
    top = wc_summary.sort_values("points", ascending=False).head(n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(top["team"], top["points"], color="#1f4e8c")
    ax.set_title(f"Top {n} Teams by Points: FIFA World Cup Final Tournaments, 2002-2022")
    ax.set_xlabel("Total points (3 for win, 1 for draw)")
    _save(fig, "07_world_cup_team_performance.png")


def chart_wc_scoring_trends(wc_matches: pd.DataFrame):
    yearly = wc_matches.groupby("year")["total_goals"].mean()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(yearly.index.astype(str), yearly.values, color="#c0392b")
    ax.set_title("Average Goals per Match by World Cup Tournament (2002-2022)")
    ax.set_xlabel("World Cup year")
    ax.set_ylabel("Average goals per match")
    for i, v in enumerate(yearly.values):
        ax.text(i, v + 0.03, f"{v:.2f}", ha="center", fontsize=9)
    _save(fig, "08_world_cup_scoring_trends.png")


def chart_goals_for_vs_against(summary: pd.DataFrame, min_matches: int = 300):
    sub = summary[summary["matches_played"] >= min_matches]
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.scatter(sub["goals_conceded_per_match"], sub["goals_scored_per_match"],
               s=sub["matches_played"] / 8, alpha=0.6, color="#1f4e8c", edgecolor="white")
    for _, row in sub.sort_values("goals_scored_per_match", ascending=False).head(8).iterrows():
        ax.annotate(row["team"], (row["goals_conceded_per_match"], row["goals_scored_per_match"]),
                    fontsize=8, xytext=(4, 2), textcoords="offset points")
    ax.set_title(f"Attack vs. Defense: Goals Scored vs. Goals Conceded per Match (min. {min_matches} matches)")
    ax.set_xlabel("Goals conceded per match")
    ax.set_ylabel("Goals scored per match")
    ax.invert_xaxis()
    _save(fig, "09_goals_for_vs_against.png")


def chart_dominance_index(tdi: pd.DataFrame, n: int = 15):
    top = tdi.sort_values("dominance_index", ascending=False).head(n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(top["team"], top["dominance_index"], color="#16a085")
    ax.set_title(f"Team Dominance Index — Top {n} (min. 300 career matches)")
    ax.set_xlabel("Dominance Index (0-100 scale)")
    _save(fig, "10_team_dominance_index.png")


def chart_consistency_vs_performance(tdi: pd.DataFrame, n: int = 20):
    sub = tdi.head(n)
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.scatter(sub["points_per_match"], sub["consistency_score"], s=60, color="#8e44ad", alpha=0.75)
    for _, row in sub.iterrows():
        ax.annotate(row["team"], (row["points_per_match"], row["consistency_score"]),
                    fontsize=8, xytext=(4, 2), textcoords="offset points")
    ax.set_title("World Cup Consistency vs. All-Time Points per Match (Top 20 by Dominance Index)")
    ax.set_xlabel("All-time points per match")
    ax.set_ylabel("World Cup consistency score (0-1)")
    _save(fig, "11_consistency_vs_performance.png")


def chart_team_tournament_heatmap(wc_tournament: pd.DataFrame, n_teams: int = 16):
    pivot = wc_tournament.pivot_table(index="team", columns="world_cup_year", values="points", fill_value=np.nan)
    totals = wc_tournament.groupby("team")["points"].sum().sort_values(ascending=False)
    top_teams = totals.head(n_teams).index
    pivot = pivot.loc[top_teams]
    fig, ax = plt.subplots(figsize=(9, 8))
    im = ax.imshow(pivot.values, cmap="YlGnBu", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([int(c) for c in pivot.columns])
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=8,
                         color="white" if val > pivot.values[~np.isnan(pivot.values)].mean() else "black")
    ax.set_title(f"Points Earned per World Cup Tournament — Top {n_teams} Teams (2002-2022)")
    ax.set_xlabel("World Cup year")
    fig.colorbar(im, ax=ax, label="Points (blank = did not qualify)")
    _save(fig, "12_team_tournament_heatmap.png")


def generate_all(matches, summary, wc_summary, wc_matches, wc_tournament, tdi):
    for old_png in FIGURES_DIR.glob("*.png"):
        old_png.unlink()
    chart_matches_by_year(matches)
    chart_avg_goals_over_time(matches)
    chart_top_teams_by_wins(summary)
    chart_top_teams_by_win_rate(summary)
    chart_top_teams_by_goal_diff(summary)
    chart_most_dominant_wins(summary)
    chart_wc_team_performance(wc_summary)
    chart_wc_scoring_trends(wc_matches)
    chart_goals_for_vs_against(summary)
    chart_dominance_index(tdi)
    chart_consistency_vs_performance(tdi)
    chart_team_tournament_heatmap(wc_tournament)
    print(f"Saved {len(list(FIGURES_DIR.glob('*.png')))} figures to outputs/figures")
