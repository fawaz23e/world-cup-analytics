-- analysis_queries.sql
-- Genuine, runnable PostgreSQL queries against the schema in schema.sql.
-- These mirror (not replace) the pandas analysis in the notebooks --
-- intended to demonstrate the SQL/PostgreSQL component referenced in
-- the project's tech stack.

-- 1. Top 15 teams by total wins (all international matches).
SELECT team, COUNT(*) AS matches_played, SUM(win::int) AS wins
FROM team_matches
GROUP BY team
HAVING COUNT(*) >= 300
ORDER BY wins DESC
LIMIT 15;

-- 2. World Cup win rate, 2002-2022 (minimum 10 World Cup matches played).
SELECT
    team,
    COUNT(*) AS wc_matches,
    SUM(win::int) AS wc_wins,
    ROUND(SUM(win::int)::numeric / COUNT(*), 3) AS win_rate
FROM team_matches
WHERE is_world_cup = TRUE AND world_cup_year BETWEEN 2002 AND 2022
GROUP BY team
HAVING COUNT(*) >= 10
ORDER BY win_rate DESC
LIMIT 15;

-- 3. Average goal differential per match (min. 300 matches).
SELECT
    team,
    COUNT(*) AS matches_played,
    ROUND(AVG(goal_difference)::numeric, 3) AS avg_goal_diff
FROM team_matches
GROUP BY team
HAVING COUNT(*) >= 300
ORDER BY avg_goal_diff DESC
LIMIT 15;

-- 4. Dominant-win rankings (margin >= 3 goals), min. 300 matches.
SELECT
    team,
    COUNT(*) AS matches_played,
    SUM(dominant_win::int) AS dominant_wins,
    ROUND(SUM(dominant_win::int)::numeric / COUNT(*), 3) AS dominant_win_rate
FROM team_matches
GROUP BY team
HAVING COUNT(*) >= 300
ORDER BY dominant_wins DESC
LIMIT 15;

-- 5. Tournament-by-tournament World Cup performance (one row per team per WC year).
SELECT
    team,
    world_cup_year,
    COUNT(*) AS matches_played,
    SUM(win::int) AS wins,
    SUM(draw::int) AS draws,
    SUM(loss::int) AS losses,
    SUM(points) AS points,
    ROUND(SUM(points)::numeric / COUNT(*), 3) AS points_per_match
FROM team_matches
WHERE is_world_cup = TRUE AND world_cup_year BETWEEN 2002 AND 2022
GROUP BY team, world_cup_year
ORDER BY world_cup_year, points DESC;

-- 6. Average goals per match, by World Cup tournament year (scoring trend).
SELECT
    world_cup_year,
    COUNT(*) AS matches,
    ROUND(AVG(total_goals)::numeric, 3) AS avg_goals_per_match
FROM matches
WHERE is_world_cup = TRUE AND world_cup_year BETWEEN 2002 AND 2022
GROUP BY world_cup_year
ORDER BY world_cup_year;

-- 7. Home-field advantage check: home win rate, neutral vs. non-neutral venues.
SELECT
    neutral_match,
    COUNT(*) AS matches,
    ROUND(AVG((match_result = 'home_win')::int)::numeric, 3) AS home_win_rate,
    ROUND(AVG((match_result = 'draw')::int)::numeric, 3) AS draw_rate
FROM matches
GROUP BY neutral_match;
