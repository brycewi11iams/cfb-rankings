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

CREATE OR REPLACE VIEW team_game_stats AS (
SELECT
	tg.team_id,
	tg.opp_id,
	tg.game_id,
	tg.season,
	tg.week,
	tg.site,
	tg.points_for,
	tg.points_against,
	s.drives AS off_drives,
	s.plays AS off_plays,
	s.yards AS off_yards,
	s.turnovers AS off_turnovers,
	o.drives AS def_drives,
	o.plays AS def_plays,
	o.yards AS def_yards,
	o.turnovers AS def_turnovers,
	ROUND(tg.points_for::NUMERIC / s.drives, 3) AS off_pts_per_drive,
	ROUND(s.yards::NUMERIC / s.drives, 3) AS off_yds_per_drive,
	ROUND(s.yards::NUMERIC / s.plays, 3) AS off_ypp,
	ROUND(s.turnovers::NUMERIC / s.drives, 3) AS off_to_per_drive,
	ROUND(tg.points_against::NUMERIC / o.drives, 3) AS def_pts_per_drive,
	ROUND(o.yards::NUMERIC / o.drives, 3) AS def_yds_per_drive,
	ROUND(o.yards::NUMERIC / o.plays, 3) AS def_ypp,
	ROUND(o.turnovers::NUMERIC / o.drives, 3) AS def_to_per_drive
FROM team_games tg
JOIN stats s ON tg.team_id = s.team_id AND tg.game_id = s.game_id
JOIN stats o ON tg.opp_id = o.team_id AND tg.game_id = o.game_id
);

CREATE OR REPLACE VIEW team_game_opp_record AS (
SELECT
	tg.team_id,
	tg.opp_id,
	tg.game_id,
	tg.season,
	tg.week,
	tg.result,
	r.classification AS opp_classification,
	r.wins - CASE WHEN tg.RESULT = 'L' THEN 1 ELSE 0 END AS opp_wins,
	r.losses - CASE WHEN tg.RESULT = 'W' THEN 1 ELSE 0 END AS opp_losses,
	(r.wins - CASE WHEN tg.RESULT = 'L' THEN 1 ELSE 0 END + r.losses - CASE WHEN tg.RESULT = 'W' THEN 1 ELSE 0 END) AS opp_games,
	ROUND((r.wins - CASE WHEN tg.RESULT = 'L' THEN 1 ELSE 0 END)::NUMERIC / (NULLIF(r.wins - CASE WHEN tg.RESULT = 'L' THEN 1 ELSE 0 END + r.losses - CASE WHEN tg.RESULT = 'W' THEN 1 ELSE 0 END, 0)), 3) AS opp_win_pct
FROM  team_games tg
JOIN team_records r ON r.team_id = tg.opp_id AND r.season = tg.season
);

CREATE OR REPLACE VIEW team_sos AS (
SELECT
	t.team_id,
	t.team_name,
	tg.season,
	COUNT(g.game_id) AS games,
	COUNT(g.game_id) FILTER (WHERE opp_classification = 'FBS') AS fbs_games,
	COUNT(g.game_id) FILTER (WHERE opp_classification = 'FCS') AS fcs_games,
	ROUND(AVG(opp_win_pct) FILTER (WHERE opp_classification = 'FBS'), 3) AS avg_opp_win_pct
FROM teams t
JOIN team_game_opp_record tg ON t.team_id = tg.team_id
JOIN games g ON g.game_id = tg.game_id
WHERE classification = 'FBS'
GROUP BY t.team_id, team_name, tg.season
);