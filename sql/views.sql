CREATE OR REPLACE VIEW completed_games AS (
SELECT *
FROM games
WHERE home_points IS NOT NULL AND away_points IS NOT NULL
);

CREATE OR REPLACE VIEW team_games AS (
SELECT 
	home_team_id AS team_id,
	away_team_id AS opp_id,
	home_points AS points_for,
	away_points AS points_against,
	game_id,
	season,
	week,
	game_date,
	(home_points - away_points) AS margin,
	CASE WHEN neutral_site IS TRUE THEN 'N'
	ELSE 'H' END AS site,
	CASE WHEN home_points > away_points THEN 'W'
	ELSE 'L' END AS result
FROM completed_games
UNION ALL
SELECT 
	away_team_id AS team_id,
	home_team_id AS opp_id,
	away_points AS points_for,
	home_points AS points_against,
	game_id,
	season,
	week,
	game_date,
	(away_points - home_points) AS margin,
	CASE WHEN neutral_site IS TRUE THEN 'N'
	ELSE 'A' END AS site,
	CASE WHEN away_points > home_points THEN 'W'
	ELSE 'L' END AS result
FROM completed_games
);

CREATE OR REPLACE VIEW team_records AS (
SELECT 
	tg.team_id,
	classification,
	team_name,
	season,
	COUNT(*) FILTER (WHERE RESULT = 'W') AS wins,
	COUNT(*) FILTER (WHERE RESULT = 'L') AS losses,
	ROUND(AVG(margin),2) AS avg_margin,
	COUNT(*) FILTER (WHERE RESULT = 'W' AND site = 'H') AS home_wins,
	COUNT(*) FILTER (WHERE RESULT = 'L' AND site = 'H') AS home_losses,
	COUNT(*) FILTER (WHERE RESULT = 'W' AND site = 'A') AS away_wins,
	COUNT(*) FILTER (WHERE RESULT = 'L' AND site = 'A') AS away_losses
FROM team_games tg
INNER JOIN teams t
ON tg.team_id = t.team_id
GROUP BY team_name, season, tg.team_id, classification
);


