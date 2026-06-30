# Tableau Calculated Fields

Create these calculated fields in Tableau. Field names assume the table names
from `tableau_data_model.md`.

## Core Match Measures

### Total Matches

```text
COUNTD([match_id])
```

### Total Goals

```text
SUM([total_goals])
```

### Average Goals per Match

```text
SUM([total_goals]) / COUNTD([match_id])
```

### Teams Covered

```text
COUNTD([team])
```

## Team Performance Measures

Use these on the Team Matches table.

### Wins

```text
SUM(IIF([win], 1, 0))
```

### Draws

```text
SUM(IIF([draw], 1, 0))
```

### Losses

```text
SUM(IIF([loss], 1, 0))
```

### Matches Played

```text
COUNT([team])
```

### Win Rate

```text
SUM(IIF([win], 1, 0)) / COUNT([team])
```

### Points

```text
SUM([points])
```

### Points per Match

```text
SUM([points]) / COUNT([team])
```

### Goals For

```text
SUM([goals_for])
```

### Goals Against

```text
SUM([goals_against])
```

### Goal Differential

```text
SUM([goals_for]) - SUM([goals_against])
```

### Average Goal Differential

```text
AVG([goal_difference])
```

### Dominant Wins

```text
SUM(IIF([dominant_win], 1, 0))
```

### Dominant Win Rate

```text
SUM(IIF([dominant_win], 1, 0)) / COUNT([team])
```

## World Cup Filters

### Is World Cup 2002-2022

```text
[is_world_cup]
AND [year] >= 2002
AND [year] <= 2022
```

### World Cup Year Label

```text
STR(INT([world_cup_year]))
```

Use this only after filtering out null `world_cup_year` values.

## Ranking Helpers

### Dominance Index Rank

Use Tableau's quick table calculation:

```text
RANK_DENSE(SUM([dominance_index]), 'desc')
```

### World Cup Points Rank

```text
RANK_DENSE(SUM([points]), 'desc')
```

## Goal Event Measures

Use these on the Goalscorers table.

### Scorer Goals

```text
COUNT([scorer])
```

### Penalty Goals

```text
SUM(IIF([penalty], 1, 0))
```

### Own Goals

```text
SUM(IIF([own_goal], 1, 0))
```

### Goal Minute Bin

```text
IF ISNULL([minute]) THEN "Unknown"
ELSEIF [minute] <= 15 THEN "01-15"
ELSEIF [minute] <= 30 THEN "16-30"
ELSEIF [minute] <= 45 THEN "31-45"
ELSEIF [minute] <= 60 THEN "46-60"
ELSEIF [minute] <= 75 THEN "61-75"
ELSEIF [minute] <= 90 THEN "76-90"
ELSE "90+"
END
```

## Display Formatting

- Format rates as percentages with one decimal place.
- Format Dominance Index with one decimal place.
- Format points per match and average goals per match with two decimal places.
