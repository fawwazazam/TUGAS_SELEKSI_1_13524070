USE mpl_indonesia;

-- Query Optimasi 1: award summary by season and team.
-- Fungsi:
--   Menghitung jumlah penghargaan yang diterima setiap tim pada Season 16.
-- Optimasi:
--   Query analitik award sering dimulai dari filter season_number, sedangkan
--   primary key roster_award diawali person_id. Tanpa index tambahan, DBMS
--   harus membaca lebih banyak baris roster_award sebelum memfilter season.
--   Query setelah optimasi memakai FORCE INDEX agar MariaDB memilih index
--   season-based yang memang ditujukan untuk pola query ini. Output sebelum
--   dan sesudah optimasi tetap sama, tetapi akses roster_award menjadi lebih
--   terarah berdasarkan season_number.

DROP INDEX IF EXISTS idx_roster_award_season_team ON roster_award;
DROP INDEX IF EXISTS idx_roster_award_season_award ON roster_award;

EXPLAIN
SELECT
  ra.season_number,
  t.team_name,
  COUNT(*) AS award_count
FROM roster_award ra
JOIN team t ON t.team_id = ra.team_id
WHERE ra.season_number = 16
GROUP BY ra.season_number, t.team_name
ORDER BY award_count DESC, t.team_name;

SELECT
  ra.season_number,
  t.team_name,
  COUNT(*) AS award_count
FROM roster_award ra
JOIN team t ON t.team_id = ra.team_id
WHERE ra.season_number = 16
GROUP BY ra.season_number, t.team_name
ORDER BY award_count DESC, t.team_name;

CREATE INDEX idx_roster_award_season_team
  ON roster_award (season_number, team_id, award_type_id, person_id);

EXPLAIN
SELECT
  ra.season_number,
  t.team_name,
  COUNT(*) AS award_count
FROM roster_award ra FORCE INDEX (idx_roster_award_season_team)
JOIN team t ON t.team_id = ra.team_id
WHERE ra.season_number = 16
GROUP BY ra.season_number, t.team_name
ORDER BY award_count DESC, t.team_name;

SELECT
  ra.season_number,
  t.team_name,
  COUNT(*) AS award_count
FROM roster_award ra FORCE INDEX (idx_roster_award_season_team)
JOIN team t ON t.team_id = ra.team_id
WHERE ra.season_number = 16
GROUP BY ra.season_number, t.team_name
ORDER BY award_count DESC, t.team_name;


-- Query Optimasi 2: team match history lookup.
-- Fungsi:
--   Menampilkan riwayat pertandingan sebuah tim pada season tertentu, termasuk
--   lawan dan skor kedua tim.
-- Optimasi:
--   Query ini memfilter pertandingan berdasarkan season_number, lalu membaca
--   atribut match untuk ditampilkan. Index tambahan pada matches menjadi
--   covering index untuk pola filter season + output detail match.

-- MariaDB membutuhkan index pada matches.season_number untuk foreign key
-- fk_match_season. Index kecil berikut menjaga foreign key tetap punya index
-- pendukung, sehingga index optimasi detail bisa dihapus saat reset demo.
CREATE INDEX IF NOT EXISTS idx_matches_season_fk
  ON matches (season_number);

DROP INDEX IF EXISTS idx_matches_season_detail ON matches;

EXPLAIN
SELECT
  m.season_number,
  m.stage,
  m.week,
  m.match_day,
  m.round_name,
  t.team_name,
  opponent.team_name AS opponent_team_name,
  mt.score AS team_score,
  opponent_mt.score AS opponent_score
FROM team t
JOIN match_team mt ON mt.team_id = t.team_id
JOIN matches m ON m.match_id = mt.match_id
JOIN match_team opponent_mt
  ON opponent_mt.match_id = mt.match_id
  AND opponent_mt.team_id <> mt.team_id
JOIN team opponent ON opponent.team_id = opponent_mt.team_id
WHERE t.team_name = 'ONIC'
  AND m.season_number = 17
ORDER BY m.match_id;

SELECT
  m.season_number,
  m.stage,
  m.week,
  m.match_day,
  m.round_name,
  t.team_name,
  opponent.team_name AS opponent_team_name,
  mt.score AS team_score,
  opponent_mt.score AS opponent_score
FROM team t
JOIN match_team mt ON mt.team_id = t.team_id
JOIN matches m ON m.match_id = mt.match_id
JOIN match_team opponent_mt
  ON opponent_mt.match_id = mt.match_id
  AND opponent_mt.team_id <> mt.team_id
JOIN team opponent ON opponent.team_id = opponent_mt.team_id
WHERE t.team_name = 'ONIC'
  AND m.season_number = 17
ORDER BY m.match_id;

CREATE INDEX idx_matches_season_detail
  ON matches (season_number, match_id, stage, week, match_day, round_name);

EXPLAIN
SELECT
  m.season_number,
  m.stage,
  m.week,
  m.match_day,
  m.round_name,
  t.team_name,
  opponent.team_name AS opponent_team_name,
  mt.score AS team_score,
  opponent_mt.score AS opponent_score
FROM team t
JOIN match_team mt ON mt.team_id = t.team_id
JOIN matches m FORCE INDEX (idx_matches_season_detail) ON m.match_id = mt.match_id
JOIN match_team opponent_mt
  ON opponent_mt.match_id = mt.match_id
  AND opponent_mt.team_id <> mt.team_id
JOIN team opponent ON opponent.team_id = opponent_mt.team_id
WHERE t.team_name = 'ONIC'
  AND m.season_number = 17
ORDER BY m.match_id;

SELECT
  m.season_number,
  m.stage,
  m.week,
  m.match_day,
  m.round_name,
  t.team_name,
  opponent.team_name AS opponent_team_name,
  mt.score AS team_score,
  opponent_mt.score AS opponent_score
FROM team t
JOIN match_team mt ON mt.team_id = t.team_id
JOIN matches m FORCE INDEX (idx_matches_season_detail) ON m.match_id = mt.match_id
JOIN match_team opponent_mt
  ON opponent_mt.match_id = mt.match_id
  AND opponent_mt.team_id <> mt.team_id
JOIN team opponent ON opponent.team_id = opponent_mt.team_id
WHERE t.team_name = 'ONIC'
  AND m.season_number = 17
ORDER BY m.match_id;


-- Query Optimasi 3: roster lookup by season, team, and roster status.
-- Fungsi:
--   Menampilkan roster utama sebuah tim pada season tertentu.
-- Optimasi:
--   Primary key roster diawali person_id, sedangkan query roster biasanya
--   difilter berdasarkan season_number, team_id, dan roster_status. Index
--   tambahan ini membuat akses roster per tim-season lebih efisien.

DROP INDEX IF EXISTS idx_roster_team_season_status ON roster;

EXPLAIN
SELECT
  r.season_number,
  t.team_name,
  p.person_name,
  r.roster_status,
  r.roster_role
FROM team t
JOIN roster r ON r.team_id = t.team_id
JOIN person p ON p.person_id = r.person_id
WHERE t.team_name = 'Bigetron'
  AND r.season_number = 17
  AND r.roster_status = 'main'
ORDER BY r.roster_role, p.person_name;

SELECT
  r.season_number,
  t.team_name,
  p.person_name,
  r.roster_status,
  r.roster_role
FROM team t
JOIN roster r ON r.team_id = t.team_id
JOIN person p ON p.person_id = r.person_id
WHERE t.team_name = 'Bigetron'
  AND r.season_number = 17
  AND r.roster_status = 'main'
ORDER BY r.roster_role, p.person_name;

CREATE INDEX idx_roster_team_season_status
  ON roster (team_id, season_number, roster_status, roster_role, person_id);

EXPLAIN
SELECT
  r.season_number,
  t.team_name,
  p.person_name,
  r.roster_status,
  r.roster_role
FROM team t
JOIN roster r ON r.team_id = t.team_id
JOIN person p ON p.person_id = r.person_id
WHERE t.team_name = 'Bigetron'
  AND r.season_number = 17
  AND r.roster_status = 'main'
ORDER BY r.roster_role, p.person_name;

SELECT
  r.season_number,
  t.team_name,
  p.person_name,
  r.roster_status,
  r.roster_role
FROM team t
JOIN roster r ON r.team_id = t.team_id
JOIN person p ON p.person_id = r.person_id
WHERE t.team_name = 'Bigetron'
  AND r.season_number = 17
  AND r.roster_status = 'main'
ORDER BY r.roster_role, p.person_name;
