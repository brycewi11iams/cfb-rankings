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

CREATE OR REPLACE VIEW team_tier AS (
	SELECT
		t.team_id,
		sl.season,
		tc.conference,
		CASE WHEN tc.conference IN ('SEC', 'Big Ten', 'Big 12', 'ACC') THEN 'P4'
		WHEN t.team_id = 87 THEN 'P4'
		ELSE 'G6' END AS tier
	FROM teams t
	CROSS JOIN(SELECT DISTINCT season FROM team_conferences) AS sl
	LEFT JOIN team_conferences tc ON t.team_id = tc.team_id AND tc.season = sl.season
	WHERE t.classification = 'FBS'
);

CREATE OR REPLACE VIEW team_game_tier AS (
SELECT
    tg.team_id,
    tg.opp_id,
    tg.game_id,
    tg.season,
    tg.week,
    tg.result,
    CASE WHEN o.classification = 'FCS' THEN 'FCS'
         ELSE tt.tier END AS opp_tier,
    CASE WHEN o.classification = 'FCS' AND tg.result = 'L' THEN 'G6'
         WHEN o.classification = 'FCS' THEN NULL
         ELSE tt.tier END AS counts_as
FROM team_games tg
JOIN teams t ON t.team_id = tg.team_id
JOIN teams o ON o.team_id = tg.opp_id
LEFT JOIN team_tier tt ON tt.team_id = tg.opp_id AND tt.season = tg.season
WHERE t.classification = 'FBS'
);

CREATE OR REPLACE VIEW team_asof_record AS (
SELECT
	tt.team_id,
	tt.season,
	w.as_of_week,
	COUNT(*) FILTER (WHERE g.counts_as = 'P4' AND g.RESULT = 'W') AS p4_wins,
	COUNT(*) FILTER (WHERE g.counts_as = 'P4' AND g.RESULT = 'L') AS p4_losses,
	COUNT(*) FILTER (WHERE g.counts_as = 'G6' AND g.RESULT = 'W') AS g6_wins,
	COUNT(*) FILTER (WHERE g.counts_as = 'G6' AND g.RESULT = 'L') AS g6_losses,
	COUNT(*) FILTER (WHERE g.counts_as = 'P4') AS p4_games,
	COUNT(*) FILTER (WHERE g.counts_as = 'G6') AS g6_games,
	(COUNT(*) FILTER (WHERE g.counts_as = 'P4' AND g.RESULT = 'W'))::NUMERIC / NULLIF(COUNT(*) FILTER (WHERE g.counts_as = 'P4'), 0) AS p4_win_pct,
	(COUNT(*) FILTER (WHERE g.counts_as = 'G6' AND g.RESULT = 'W'))::NUMERIC / NULLIF(COUNT(*) FILTER (WHERE g.counts_as = 'G6'), 0) AS g6_win_pct
	FROM team_tier tt
	JOIN (SELECT DISTINCT season, week AS as_of_week FROM team_game_tier) AS w ON w.season = tt.season
	LEFT JOIN team_game_tier g ON tt.team_id = g.team_id AND tt.season = g.season AND g.week <= as_of_week
	GROUP BY tt.team_id, tt.season, as_of_week
);

CREATE OR REPLACE VIEW team_game_opp_asof AS (
SELECT
	x.team_id,
	x.opp_id,
	x.game_id,
	x.season,
	x.week,
	x.as_of_week,
	x.result,
	x.opp_tier,
	x.opp_wins,
	x.opp_losses,
	x.opp_games,
	x.opp_wins::NUMERIC / NULLIF(x.opp_games, 0) AS opp_win_pct
FROM (
	SELECT
		tg.team_id,
		tg.opp_id,
		tg.game_id,
		tg.season,
		tg.week,
		tr.as_of_week,
		tg.result,
		tg.opp_tier,
		CASE WHEN tg.result = 'L'
			THEN (tr.p4_wins + tr.g6_wins) - 1
			ELSE (tr.p4_wins + tr.g6_wins)
		END AS opp_wins,
		CASE WHEN tg.result = 'W'
			THEN (tr.p4_losses + tr.g6_losses) - 1
			ELSE (tr.p4_losses + tr.g6_losses)
		END AS opp_losses,
		(tr.p4_wins + tr.g6_wins + tr.p4_losses + tr.g6_losses) - 1 AS opp_games
	FROM team_game_tier tg
	JOIN team_asof_record tr
		ON tr.team_id = tg.opp_id
		AND tr.season = tg.season
		AND tr.as_of_week >= tg.week
	WHERE tg.opp_tier != 'FCS'
) AS x
);

CREATE OR REPLACE VIEW team_asof_opp_avg AS (
SELECT
	c.team_id,
	c.season,
	c.as_of_week,
	COUNT(tgt.game_id) FILTER(WHERE tgt.opp_tier = 'P4') AS p4_opp_games,
	COUNT(tgt.game_id) FILTER(WHERE tgt.opp_tier = 'G6') AS g6_opp_games,
	AVG(tgt.opp_win_pct) FILTER(WHERE tgt.opp_tier = 'P4') AS p4_opp_wp,
	AVG(tgt.opp_win_pct) FILTER(WHERE tgt.opp_tier = 'G6') AS g6_opp_wp
FROM team_asof_record c
LEFT JOIN team_game_opp_asof tgt ON c.team_id = tgt.team_id AND c.season = tgt.season AND c.as_of_week = tgt.as_of_week
GROUP BY c.team_id, c.season, c.as_of_week
);

CREATE OR REPLACE VIEW team_asof_oopp_avg AS (
SELECT
	b.team_id,
	b.season,
	b.as_of_week,
	AVG(o.p4_opp_wp) FILTER (WHERE g.opp_tier = 'P4') AS p4_oopp_wp,
	AVG(o.g6_opp_wp) FILTER (WHERE g.opp_tier = 'G6') AS g6_oopp_wp
FROM team_asof_opp_avg b
LEFT JOIN team_game_opp_asof g
	ON g.team_id = b.team_id
	AND g.season = b.season
	AND g.as_of_week = b.as_of_week
LEFT JOIN team_asof_opp_avg o
	ON o.team_id = g.opp_id
	AND o.season = g.season
	AND o.as_of_week = g.as_of_week
GROUP BY b.team_id, b.season, b.as_of_week
);

