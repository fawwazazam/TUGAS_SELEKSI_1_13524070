USE mpl_indonesia;

SELECT COUNT(*) AS season_count FROM season;
SELECT COUNT(*) AS season_location_count FROM season_location;
SELECT COUNT(*) AS team_count FROM team;
SELECT COUNT(*) AS person_count FROM person;
SELECT COUNT(*) AS match_count FROM matches;
SELECT COUNT(*) AS roster_count FROM roster;
SELECT COUNT(*) AS roster_award_count FROM roster_award;

SELECT
  s.season_number,
  s.start_date,
  s.end_date,
  t.team_name,
  ts.final_rank,
  ts.match_wins,
  ts.match_losses,
  ts.game_wins,
  ts.game_losses,
  CAST(ts.game_wins AS SIGNED) - CAST(ts.game_losses AS SIGNED) AS game_diff
FROM team_season ts
JOIN season s ON s.season_number = ts.season_number
JOIN team t ON t.team_id = ts.team_id
WHERE s.season_number = 17
ORDER BY ts.final_rank;

SELECT
  p.person_name,
  t.team_name,
  r.roster_status,
  r.roster_role
FROM roster r
JOIN person p ON p.person_id = r.person_id
JOIN team t ON t.team_id = r.team_id
WHERE r.season_number = 17
  AND t.team_name = 'Bigetron'
ORDER BY r.roster_status, p.person_name;

SELECT
  m.match_id,
  m.stage,
  m.week,
  m.match_day,
  m.round_name,
  t.team_name,
  mt.side,
  mt.score
FROM match_team mt
JOIN matches m ON m.match_id = mt.match_id
JOIN team t ON t.team_id = mt.team_id
WHERE m.season_number = 17
ORDER BY m.match_id, mt.side
LIMIT 20;

SELECT
  p.person_name,
  t.team_name,
  s.season_number,
  a.award_name
FROM roster_award ra
JOIN roster r
  ON r.person_id = ra.person_id
  AND r.season_number = ra.season_number
  AND r.team_id = ra.team_id
JOIN person p ON p.person_id = r.person_id
JOIN team t ON t.team_id = r.team_id
JOIN season s ON s.season_number = r.season_number
JOIN award_type a ON a.award_type_id = ra.award_type_id
WHERE s.season_number >= 15
ORDER BY s.season_number, a.award_name, p.person_name;

SELECT
  a.award_name,
  r.season_number,
  COUNT(*) AS recipient_count,
  COUNT(DISTINCT r.roster_role) AS role_count
FROM roster_award ra
JOIN roster r
  ON r.person_id = ra.person_id
  AND r.season_number = ra.season_number
  AND r.team_id = ra.team_id
JOIN award_type a ON a.award_type_id = ra.award_type_id
WHERE a.award_name IN ('Dream Team', 'First Team', 'Second Team')
GROUP BY a.award_name, r.season_number
ORDER BY a.award_name, r.season_number;
