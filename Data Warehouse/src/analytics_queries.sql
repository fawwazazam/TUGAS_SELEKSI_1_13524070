-- Example analytics queries for validating and presenting the warehouse.

USE mpl_indonesia_dw;

SELECT COUNT(*) AS season_count FROM dim_season;
SELECT COUNT(*) AS team_count FROM dim_team;
SELECT COUNT(*) AS person_count FROM dim_person;
SELECT COUNT(*) AS match_dimension_count FROM dim_match;
SELECT COUNT(*) AS team_match_fact_count FROM fact_team_match;
SELECT COUNT(*) AS team_season_fact_count FROM fact_team_season;
SELECT COUNT(*) AS award_fact_count FROM fact_award;

SELECT
  ds.season_number,
  dt.team_name,
  fts.final_rank,
  fts.match_wins,
  fts.match_losses,
  fts.match_win_rate,
  fts.game_wins,
  fts.game_losses,
  fts.game_diff
FROM fact_team_season fts
JOIN dim_season ds ON ds.season_key = fts.season_key
JOIN dim_team dt ON dt.team_key = fts.team_key
WHERE ds.season_number = 17
ORDER BY fts.final_rank;

SELECT
  dt.team_name,
  COUNT(*) AS match_played,
  SUM(ftm.is_winner) AS match_won,
  ROUND(SUM(ftm.is_winner) / COUNT(*) * 100, 2) AS win_rate,
  SUM(ftm.score_for) AS total_score_for,
  SUM(ftm.score_against) AS total_score_against,
  SUM(ftm.score_diff) AS total_score_diff
FROM fact_team_match ftm
JOIN dim_team dt ON dt.team_key = ftm.team_key
GROUP BY dt.team_name
ORDER BY match_won DESC, total_score_diff DESC, dt.team_name;

SELECT
  dat.award_name,
  dr.role_name,
  COUNT(*) AS recipient_count
FROM fact_award fa
JOIN dim_award_type dat ON dat.award_type_key = fa.award_type_key
JOIN dim_role dr ON dr.role_key = fa.role_key
WHERE dat.award_group = 'Team Selection'
GROUP BY dat.award_name, dr.role_name
ORDER BY dat.award_name, dr.role_name;

SELECT
  dp.person_name,
  dt.team_name,
  COUNT(*) AS award_count
FROM fact_award fa
JOIN dim_person dp ON dp.person_key = fa.person_key
JOIN dim_team dt ON dt.team_key = fa.team_key
GROUP BY dp.person_name, dt.team_name
HAVING COUNT(*) >= 2
ORDER BY award_count DESC, dp.person_name;
