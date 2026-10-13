/*
DROP TABLE IF EXISTS stats CASCADE;
DROP TABLE IF EXISTS games CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
*/

CREATE TABLE teams(
	team_id INTEGER,
	team_name VARCHAR(60) NOT NULL,
	classification VARCHAR(5) NOT NULL,
	CONSTRAINT pk_teams PRIMARY KEY (team_id),
	CONSTRAINT ck_classification CHECK (classification IN ('FBS', 'FCS'))
);

CREATE TABLE games(
	game_id INTEGER,
	season INTEGER NOT NULL,
	week INTEGER NOT NULL,
	game_date date NOT NULL,
	home_team_id INTEGER NOT NULL,
	away_team_id INTEGER NOT NULL,
	home_points INTEGER,
	away_points INTEGER,
	neutral_site BOOLEAN NOT NULL DEFAULT False,
	CONSTRAINT pk_games PRIMARY KEY (game_id),
	CONSTRAINT fk_home_team FOREIGN KEY (home_team_id)
		REFERENCES teams (team_id),
	CONSTRAINT fk_away_team FOREIGN KEY (away_team_id)
		REFERENCES teams (team_id),
	CONSTRAINT ck_teams_dif CHECK (home_team_id <> away_team_id),
	CONSTRAINT ck_teams_both_or_neither CHECK (
	(home_points IS NULL AND away_points IS NULL)
	OR
	(home_points IS NOT NULL AND away_points IS NOT NULL)
	),
	CONSTRAINT ck_points_above_zero CHECK(
	(home_points >= 0) AND (away_points >= 0)
	)
);

CREATE TABLE stats(
	game_id INTEGER,
	team_id INTEGER,
	drives INTEGER NOT NULL,
	plays INTEGER NOT NULL,
	yards INTEGER NOT NULL,
	turnovers INTEGER,
	CONSTRAINT pk_stats PRIMARY KEY (game_id, team_id),
	CONSTRAINT fk_stats_game FOREIGN KEY (game_id)
		REFERENCES games (game_id),
	CONSTRAINT fk_stats_team FOREIGN KEY (team_id)
		REFERENCES teams (team_id),
	CONSTRAINT ck_drives CHECK (drives >= 0),
	CONSTRAINT ck_plays CHECK (plays >= 0),
	CONSTRAINT ck_turnovers CHECK (turnovers >= 0)
);