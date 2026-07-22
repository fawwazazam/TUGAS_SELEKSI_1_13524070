DROP DATABASE IF EXISTS mpl_indonesia;
CREATE DATABASE mpl_indonesia
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE mpl_indonesia;

CREATE TABLE season (
  season_number TINYINT UNSIGNED NOT NULL,
  name VARCHAR(100) NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  prize_pool_usd DECIMAL(12,2) NOT NULL,
  PRIMARY KEY (season_number),
  CONSTRAINT chk_season_scope CHECK (season_number BETWEEN 12 AND 17),
  CONSTRAINT chk_season_date_order CHECK (start_date <= end_date),
  CONSTRAINT chk_season_prize_pool CHECK (prize_pool_usd >= 0)
) ENGINE=InnoDB;

CREATE TABLE season_location (
  season_number TINYINT UNSIGNED NOT NULL,
  location VARCHAR(100) NOT NULL,
  PRIMARY KEY (season_number, location),
  CONSTRAINT fk_season_location_season
    FOREIGN KEY (season_number) REFERENCES season (season_number)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE team (
  team_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  team_name VARCHAR(100) NOT NULL,
  PRIMARY KEY (team_id),
  CONSTRAINT uq_team_name UNIQUE (team_name)
) ENGINE=InnoDB;

CREATE TABLE person (
  person_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  person_name VARCHAR(100) NOT NULL,
  nationality VARCHAR(80) NOT NULL,
  PRIMARY KEY (person_id),
  CONSTRAINT uq_person_name UNIQUE (person_name)
) ENGINE=InnoDB;

CREATE TABLE award_type (
  award_type_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  award_name VARCHAR(100) NOT NULL,
  PRIMARY KEY (award_type_id),
  CONSTRAINT uq_award_name UNIQUE (award_name),
  CONSTRAINT chk_award_name CHECK (
    award_name IN (
      'Regular Season MVP',
      'Finals MVP',
      'Most Improved',
      'Rising Star',
      'Rookie of The Season',
      'Dream Team',
      'First Team',
      'Second Team'
    )
  )
) ENGINE=InnoDB;

CREATE TABLE matches (
  match_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  stage VARCHAR(30) NOT NULL,
  week TINYINT UNSIGNED NULL,
  match_day TINYINT UNSIGNED NULL,
  round_name VARCHAR(80) NULL,
  season_number TINYINT UNSIGNED NOT NULL,
  PRIMARY KEY (match_id),
  CONSTRAINT fk_match_season
    FOREIGN KEY (season_number) REFERENCES season (season_number)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_match_stage CHECK (stage IN ('Regular Season', 'Playoffs')),
  CONSTRAINT chk_match_stage_fields CHECK (
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

CREATE TABLE team_season (
  season_number TINYINT UNSIGNED NOT NULL,
  team_id INT UNSIGNED NOT NULL,
  final_rank TINYINT UNSIGNED NOT NULL,
  match_wins TINYINT UNSIGNED NOT NULL,
  match_losses TINYINT UNSIGNED NOT NULL,
  game_wins TINYINT UNSIGNED NOT NULL,
  game_losses TINYINT UNSIGNED NOT NULL,
  PRIMARY KEY (season_number, team_id),
  CONSTRAINT fk_team_season_season
    FOREIGN KEY (season_number) REFERENCES season (season_number)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_team_season_team
    FOREIGN KEY (team_id) REFERENCES team (team_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT uq_team_season_rank UNIQUE (season_number, final_rank),
  CONSTRAINT chk_team_season_rank CHECK (final_rank >= 1),
  CONSTRAINT chk_team_season_match_count CHECK (match_wins + match_losses = 16),
  CONSTRAINT chk_team_season_game_count CHECK (game_wins + game_losses > 0)
) ENGINE=InnoDB;

CREATE TABLE roster (
  person_id INT UNSIGNED NOT NULL,
  season_number TINYINT UNSIGNED NOT NULL,
  team_id INT UNSIGNED NOT NULL,
  roster_status VARCHAR(10) NOT NULL,
  roster_role VARCHAR(50) NOT NULL,
  PRIMARY KEY (person_id, season_number, team_id),
  CONSTRAINT fk_roster_person
    FOREIGN KEY (person_id) REFERENCES person (person_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_roster_team_season
    FOREIGN KEY (season_number, team_id) REFERENCES team_season (season_number, team_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_roster_status CHECK (roster_status IN ('main', 'subs', 'staff')),
  CONSTRAINT chk_roster_role CHECK (
    (
      roster_status = 'main'
      AND roster_role IN ('EXP Laner', 'Gold Laner', 'Jungler', 'Mid Laner', 'Roamer')
    )
    OR (
      roster_status = 'subs'
      AND roster_role IN ('EXP Laner', 'Gold Laner', 'Jungler', 'Mid Laner', 'Roamer', 'Flex')
    )
    OR (
      roster_status = 'staff'
      AND roster_role IN ('Analyst', 'Assistant Coach', 'Coach', 'Head Coach')
    )
  )
) ENGINE=InnoDB;

CREATE TABLE match_team (
  match_id INT UNSIGNED NOT NULL,
  team_id INT UNSIGNED NOT NULL,
  side CHAR(1) NOT NULL,
  score TINYINT UNSIGNED NOT NULL,
  PRIMARY KEY (match_id, team_id),
  CONSTRAINT fk_match_team_match
    FOREIGN KEY (match_id) REFERENCES matches (match_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_match_team_team
    FOREIGN KEY (team_id) REFERENCES team (team_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT uq_match_side UNIQUE (match_id, side),
  CONSTRAINT chk_match_side CHECK (side IN ('A', 'B')),
  CONSTRAINT chk_match_score CHECK (score <= 4)
) ENGINE=InnoDB;

CREATE TABLE roster_award (
  person_id INT UNSIGNED NOT NULL,
  season_number TINYINT UNSIGNED NOT NULL,
  team_id INT UNSIGNED NOT NULL,
  award_type_id INT UNSIGNED NOT NULL,
  PRIMARY KEY (person_id, season_number, team_id, award_type_id),
  CONSTRAINT fk_roster_award_roster
    FOREIGN KEY (person_id, season_number, team_id)
    REFERENCES roster (person_id, season_number, team_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_roster_award_award_type
    FOREIGN KEY (award_type_id) REFERENCES award_type (award_type_id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

DELIMITER //

CREATE TRIGGER trg_match_team_participant_insert
BEFORE INSERT ON match_team
FOR EACH ROW
BEGIN
  DECLARE v_season_number TINYINT UNSIGNED;
  DECLARE v_existing_count INT DEFAULT 0;

  SELECT season_number INTO v_season_number
  FROM matches
  WHERE match_id = NEW.match_id;

  IF NOT EXISTS (
    SELECT 1
    FROM team_season
    WHERE season_number = v_season_number
      AND team_id = NEW.team_id
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'match_team team must participate in the match season';
  END IF;

  SELECT COUNT(*) INTO v_existing_count
  FROM match_team
  WHERE match_id = NEW.match_id;

  IF v_existing_count >= 2 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'a match cannot have more than two teams';
  END IF;
END//

CREATE TRIGGER trg_match_team_participant_update
BEFORE UPDATE ON match_team
FOR EACH ROW
BEGIN
  DECLARE v_season_number TINYINT UNSIGNED;

  SELECT season_number INTO v_season_number
  FROM matches
  WHERE match_id = NEW.match_id;

  IF NOT EXISTS (
    SELECT 1
    FROM team_season
    WHERE season_number = v_season_number
      AND team_id = NEW.team_id
  ) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'match_team team must participate in the match season';
  END IF;
END//

CREATE TRIGGER trg_roster_award_insert
BEFORE INSERT ON roster_award
FOR EACH ROW
BEGIN
  DECLARE v_award_name VARCHAR(100);
  DECLARE v_roster_role VARCHAR(50);

  SELECT award_name INTO v_award_name
  FROM award_type
  WHERE award_type_id = NEW.award_type_id;

  SELECT roster_role INTO v_roster_role
  FROM roster
  WHERE person_id = NEW.person_id
    AND season_number = NEW.season_number
    AND team_id = NEW.team_id;

  IF v_award_name IN ('Dream Team', 'First Team', 'Second Team') THEN
    IF v_roster_role NOT IN ('EXP Laner', 'Gold Laner', 'Jungler', 'Mid Laner', 'Roamer') THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'team awards must be assigned to a main Mobile Legends role';
    END IF;

    IF EXISTS (
      SELECT 1
      FROM roster_award ra
      JOIN roster r
        ON r.person_id = ra.person_id
        AND r.season_number = ra.season_number
        AND r.team_id = ra.team_id
      WHERE ra.award_type_id = NEW.award_type_id
        AND r.season_number = NEW.season_number
        AND r.roster_role = v_roster_role
    ) THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'team awards can only have one recipient per role per season';
    END IF;
  END IF;
END//

CREATE TRIGGER trg_roster_award_update
BEFORE UPDATE ON roster_award
FOR EACH ROW
BEGIN
  DECLARE v_award_name VARCHAR(100);
  DECLARE v_roster_role VARCHAR(50);

  SELECT award_name INTO v_award_name
  FROM award_type
  WHERE award_type_id = NEW.award_type_id;

  SELECT roster_role INTO v_roster_role
  FROM roster
  WHERE person_id = NEW.person_id
    AND season_number = NEW.season_number
    AND team_id = NEW.team_id;

  IF v_award_name IN ('Dream Team', 'First Team', 'Second Team') THEN
    IF v_roster_role NOT IN ('EXP Laner', 'Gold Laner', 'Jungler', 'Mid Laner', 'Roamer') THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'team awards must be assigned to a main Mobile Legends role';
    END IF;

    IF EXISTS (
      SELECT 1
      FROM roster_award ra
      JOIN roster r
        ON r.person_id = ra.person_id
        AND r.season_number = ra.season_number
        AND r.team_id = ra.team_id
      WHERE ra.award_type_id = NEW.award_type_id
        AND r.season_number = NEW.season_number
        AND r.roster_role = v_roster_role
        AND NOT (
          ra.person_id = OLD.person_id
          AND ra.season_number = OLD.season_number
          AND ra.team_id = OLD.team_id
          AND ra.award_type_id = OLD.award_type_id
        )
    ) THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'team awards can only have one recipient per role per season';
    END IF;
  END IF;
END//

DELIMITER ;
