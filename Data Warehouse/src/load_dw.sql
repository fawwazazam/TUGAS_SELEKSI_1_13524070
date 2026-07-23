-- ETL script from the normalized OLTP database into the warehouse.
-- Prerequisite: database mpl_indonesia already exists and is populated.

USE mpl_indonesia_dw;

START TRANSACTION;

INSERT INTO dim_season (
  season_number,
  season_name,
  start_date,
  end_date,
  prize_pool_usd,
  location_list
)
SELECT
  s.season_number,
  s.name,
  s.start_date,
  s.end_date,
  s.prize_pool_usd,
  GROUP_CONCAT(sl.location ORDER BY sl.location SEPARATOR ', ') AS location_list
FROM mpl_indonesia.season s
JOIN mpl_indonesia.season_location sl
  ON sl.season_number = s.season_number
GROUP BY
  s.season_number,
  s.name,
  s.start_date,
  s.end_date,
  s.prize_pool_usd
ORDER BY s.season_number;

INSERT INTO dim_team (team_name)
SELECT team_name
FROM mpl_indonesia.team
ORDER BY team_id;

INSERT INTO dim_person (person_name, nationality)
SELECT person_name, nationality
FROM mpl_indonesia.person
ORDER BY person_id;

INSERT INTO dim_award_type (award_name, award_group)
SELECT
  award_name,
  CASE
    WHEN award_name IN ('Dream Team', 'First Team', 'Second Team')
      THEN 'Team Selection'
    ELSE 'Individual'
  END AS award_group
FROM mpl_indonesia.award_type
ORDER BY award_type_id;

INSERT INTO dim_role (role_name, role_group, is_main_role)
SELECT
  roster_role,
  CASE
    WHEN roster_role IN ('Analyst', 'Assistant Coach', 'Coach', 'Head Coach')
      THEN 'Staff Role'
    ELSE 'Player Role'
  END AS role_group,
  roster_role IN ('EXP Laner', 'Gold Laner', 'Jungler', 'Mid Laner', 'Roamer') AS is_main_role
FROM (
  SELECT DISTINCT roster_role
  FROM mpl_indonesia.roster
) roles
ORDER BY roster_role;

INSERT INTO dim_match (match_id, stage, week, match_day, round_name)
SELECT match_id, stage, week, match_day, round_name
FROM mpl_indonesia.matches
ORDER BY match_id;

INSERT INTO fact_team_season (
  season_key,
  team_key,
  final_rank,
  match_wins,
  match_losses,
  match_count,
  match_win_rate,
  game_wins,
  game_losses,
  game_count,
  game_win_rate,
  game_diff
)
SELECT
  ds.season_key,
  dt.team_key,
  ts.final_rank,
  ts.match_wins,
  ts.match_losses,
  ts.match_wins + ts.match_losses AS match_count,
  ROUND(ts.match_wins / (ts.match_wins + ts.match_losses) * 100, 2) AS match_win_rate,
  ts.game_wins,
  ts.game_losses,
  ts.game_wins + ts.game_losses AS game_count,
  ROUND(ts.game_wins / (ts.game_wins + ts.game_losses) * 100, 2) AS game_win_rate,
  CAST(ts.game_wins AS SIGNED) - CAST(ts.game_losses AS SIGNED) AS game_diff
FROM mpl_indonesia.team_season ts
JOIN mpl_indonesia.team t
  ON t.team_id = ts.team_id
JOIN dim_season ds
  ON ds.season_number = ts.season_number
JOIN dim_team dt
  ON dt.team_name = t.team_name
ORDER BY ts.season_number, ts.final_rank;

INSERT INTO fact_team_match (
  season_key,
  match_key,
  team_key,
  opponent_team_key,
  score_for,
  score_against,
  score_diff,
  is_winner,
  match_count
)
SELECT
  ds.season_key,
  dm.match_key,
  dt.team_key,
  opponent_dt.team_key AS opponent_team_key,
  mt.score AS score_for,
  opponent_mt.score AS score_against,
  CAST(mt.score AS SIGNED) - CAST(opponent_mt.score AS SIGNED) AS score_diff,
  mt.score > opponent_mt.score AS is_winner,
  1 AS match_count
FROM mpl_indonesia.match_team mt
JOIN mpl_indonesia.match_team opponent_mt
  ON opponent_mt.match_id = mt.match_id
  AND opponent_mt.team_id <> mt.team_id
JOIN mpl_indonesia.matches m
  ON m.match_id = mt.match_id
JOIN mpl_indonesia.team t
  ON t.team_id = mt.team_id
JOIN mpl_indonesia.team opponent_t
  ON opponent_t.team_id = opponent_mt.team_id
JOIN dim_season ds
  ON ds.season_number = m.season_number
JOIN dim_match dm
  ON dm.match_id = m.match_id
JOIN dim_team dt
  ON dt.team_name = t.team_name
JOIN dim_team opponent_dt
  ON opponent_dt.team_name = opponent_t.team_name
ORDER BY mt.match_id, mt.side;

INSERT INTO fact_award (
  season_key,
  team_key,
  person_key,
  award_type_key,
  role_key,
  award_count
)
SELECT
  ds.season_key,
  dt.team_key,
  dp.person_key,
  dat.award_type_key,
  dr.role_key,
  1 AS award_count
FROM mpl_indonesia.roster_award ra
JOIN mpl_indonesia.roster r
  ON r.person_id = ra.person_id
  AND r.season_number = ra.season_number
  AND r.team_id = ra.team_id
JOIN mpl_indonesia.person p
  ON p.person_id = r.person_id
JOIN mpl_indonesia.team t
  ON t.team_id = r.team_id
JOIN mpl_indonesia.award_type a
  ON a.award_type_id = ra.award_type_id
JOIN dim_season ds
  ON ds.season_number = r.season_number
JOIN dim_team dt
  ON dt.team_name = t.team_name
JOIN dim_person dp
  ON dp.person_name = p.person_name
JOIN dim_award_type dat
  ON dat.award_name = a.award_name
JOIN dim_role dr
  ON dr.role_name = r.roster_role
ORDER BY r.season_number, a.award_name, p.person_name;

COMMIT;
