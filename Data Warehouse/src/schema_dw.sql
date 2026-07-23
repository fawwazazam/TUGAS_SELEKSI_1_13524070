-- Skema bintang untuk data warehouse MPL Indonesia.
-- Level detail data:
--   fact_team_match  = satu baris per tim dalam satu pertandingan
--   fact_team_season = satu baris per tim dalam satu musim
--   fact_award       = satu baris per penghargaan roster

DROP DATABASE IF EXISTS mpl_indonesia_dw;
CREATE DATABASE mpl_indonesia_dw
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE mpl_indonesia_dw;

CREATE TABLE dim_season (
  season_key INT UNSIGNED NOT NULL AUTO_INCREMENT,
  season_number TINYINT UNSIGNED NOT NULL,
  season_name VARCHAR(100) NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  prize_pool_usd DECIMAL(12,2) NOT NULL,
  location_list VARCHAR(255) NOT NULL,
  PRIMARY KEY (season_key),
  CONSTRAINT uq_dim_season_number UNIQUE (season_number),
  CONSTRAINT chk_dim_season_date_order CHECK (start_date <= end_date),
  CONSTRAINT chk_dim_season_prize_pool CHECK (prize_pool_usd >= 0)
) ENGINE=InnoDB;

CREATE TABLE dim_team (
  team_key INT UNSIGNED NOT NULL AUTO_INCREMENT,
  team_name VARCHAR(100) NOT NULL,
  PRIMARY KEY (team_key),
  CONSTRAINT uq_dim_team_name UNIQUE (team_name)
) ENGINE=InnoDB;

CREATE TABLE dim_person (
  person_key INT UNSIGNED NOT NULL AUTO_INCREMENT,
  person_name VARCHAR(100) NOT NULL,
  nationality VARCHAR(80) NOT NULL,
  PRIMARY KEY (person_key),
  CONSTRAINT uq_dim_person_name UNIQUE (person_name)
) ENGINE=InnoDB;

CREATE TABLE dim_award_type (
  award_type_key INT UNSIGNED NOT NULL AUTO_INCREMENT,
  award_name VARCHAR(100) NOT NULL,
  award_group VARCHAR(30) NOT NULL,
  PRIMARY KEY (award_type_key),
  CONSTRAINT uq_dim_award_name UNIQUE (award_name),
  CONSTRAINT chk_dim_award_group CHECK (award_group IN ('Individual', 'Team Selection'))
) ENGINE=InnoDB;

CREATE TABLE dim_role (
  role_key INT UNSIGNED NOT NULL AUTO_INCREMENT,
  role_name VARCHAR(50) NOT NULL,
  role_group VARCHAR(30) NOT NULL,
  is_main_role BOOLEAN NOT NULL,
  PRIMARY KEY (role_key),
  CONSTRAINT uq_dim_role_name UNIQUE (role_name),
  CONSTRAINT chk_dim_role_group CHECK (role_group IN ('Player Role', 'Staff Role'))
) ENGINE=InnoDB;

CREATE TABLE dim_match (
  match_key INT UNSIGNED NOT NULL AUTO_INCREMENT,
  match_id INT UNSIGNED NOT NULL,
  stage VARCHAR(30) NOT NULL,
  week TINYINT UNSIGNED NULL,
  match_day TINYINT UNSIGNED NULL,
  round_name VARCHAR(80) NULL,
  PRIMARY KEY (match_key),
  CONSTRAINT uq_dim_match_id UNIQUE (match_id),
  CONSTRAINT chk_dim_match_stage CHECK (stage IN ('Regular Season', 'Playoffs')),
  CONSTRAINT chk_dim_match_stage_fields CHECK (
    (
      stage = 'Regular Season'
      AND week IS NOT NULL
      AND match_day IS NOT NULL
      AND round_name IS NULL
    )
    OR (
      stage = 'Playoffs'
      AND week IS NULL
      AND match_day IS NULL
      AND round_name IS NOT NULL
    )
  )
) ENGINE=InnoDB;

CREATE TABLE fact_team_match (
  team_match_key BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  season_key INT UNSIGNED NOT NULL,
  match_key INT UNSIGNED NOT NULL,
  team_key INT UNSIGNED NOT NULL,
  opponent_team_key INT UNSIGNED NOT NULL,
  score_for TINYINT UNSIGNED NOT NULL,
  score_against TINYINT UNSIGNED NOT NULL,
  score_diff SMALLINT NOT NULL,
  is_winner BOOLEAN NOT NULL,
  match_count TINYINT UNSIGNED NOT NULL DEFAULT 1,
  PRIMARY KEY (team_match_key),
  CONSTRAINT uq_fact_team_match UNIQUE (match_key, team_key),
  CONSTRAINT fk_fact_team_match_season FOREIGN KEY (season_key) REFERENCES dim_season (season_key),
  CONSTRAINT fk_fact_team_match_match FOREIGN KEY (match_key) REFERENCES dim_match (match_key),
  CONSTRAINT fk_fact_team_match_team FOREIGN KEY (team_key) REFERENCES dim_team (team_key),
  CONSTRAINT fk_fact_team_match_opponent FOREIGN KEY (opponent_team_key) REFERENCES dim_team (team_key),
  CONSTRAINT chk_fact_team_match_count CHECK (match_count = 1),
  CONSTRAINT chk_fact_team_match_not_same_team CHECK (team_key <> opponent_team_key)
) ENGINE=InnoDB;

CREATE TABLE fact_team_season (
  team_season_key BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  season_key INT UNSIGNED NOT NULL,
  team_key INT UNSIGNED NOT NULL,
  final_rank TINYINT UNSIGNED NOT NULL,
  match_wins TINYINT UNSIGNED NOT NULL,
  match_losses TINYINT UNSIGNED NOT NULL,
  match_count TINYINT UNSIGNED NOT NULL,
  match_win_rate DECIMAL(5,2) NOT NULL,
  game_wins TINYINT UNSIGNED NOT NULL,
  game_losses TINYINT UNSIGNED NOT NULL,
  game_count TINYINT UNSIGNED NOT NULL,
  game_win_rate DECIMAL(5,2) NOT NULL,
  game_diff SMALLINT NOT NULL,
  PRIMARY KEY (team_season_key),
  CONSTRAINT uq_fact_team_season UNIQUE (season_key, team_key),
  CONSTRAINT fk_fact_team_season_season FOREIGN KEY (season_key) REFERENCES dim_season (season_key),
  CONSTRAINT fk_fact_team_season_team FOREIGN KEY (team_key) REFERENCES dim_team (team_key),
  CONSTRAINT chk_fact_team_season_match_count CHECK (match_count = match_wins + match_losses),
  CONSTRAINT chk_fact_team_season_game_count CHECK (game_count = game_wins + game_losses),
  CONSTRAINT chk_fact_team_season_match_win_rate CHECK (match_win_rate BETWEEN 0 AND 100),
  CONSTRAINT chk_fact_team_season_game_win_rate CHECK (game_win_rate BETWEEN 0 AND 100)
) ENGINE=InnoDB;

CREATE TABLE fact_award (
  award_fact_key BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  season_key INT UNSIGNED NOT NULL,
  team_key INT UNSIGNED NOT NULL,
  person_key INT UNSIGNED NOT NULL,
  award_type_key INT UNSIGNED NOT NULL,
  role_key INT UNSIGNED NOT NULL,
  award_count TINYINT UNSIGNED NOT NULL DEFAULT 1,
  PRIMARY KEY (award_fact_key),
  CONSTRAINT uq_fact_award UNIQUE (season_key, team_key, person_key, award_type_key),
  CONSTRAINT fk_fact_award_season FOREIGN KEY (season_key) REFERENCES dim_season (season_key),
  CONSTRAINT fk_fact_award_team FOREIGN KEY (team_key) REFERENCES dim_team (team_key),
  CONSTRAINT fk_fact_award_person FOREIGN KEY (person_key) REFERENCES dim_person (person_key),
  CONSTRAINT fk_fact_award_type FOREIGN KEY (award_type_key) REFERENCES dim_award_type (award_type_key),
  CONSTRAINT fk_fact_award_role FOREIGN KEY (role_key) REFERENCES dim_role (role_key),
  CONSTRAINT chk_fact_award_count CHECK (award_count = 1)
) ENGINE=InnoDB;
