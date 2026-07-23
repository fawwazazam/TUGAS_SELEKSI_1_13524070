# Data Historis MPL Indonesia Season 12-17

## Author

- Nama: A. Fawwaz Azam Wicaksono
- NIM: 13524070

## Deskripsi

Proyek ini melakukan proses ETL untuk data historis MPL Indonesia Season 12 sampai Season 17 dari Liquipedia. Data yang diambil meliputi season, tim, standings akhir regular season, roster pemain/staff, award pemain, dan hasil pertandingan.

Topik ini dipilih karena MPL Indonesia memiliki data historis yang cukup terstruktur, tetapi nama tim dan format tabelnya tidak selalu konsisten antar season. Hal itu membuat datanya cocok untuk latihan scraping, pembersihan data, perancangan basis data relasional, dan analisis historis.

Topik awal yang didaftarkan adalah data historis MPL Indonesia Season 1-17 berdasarkan tim, pemain, pertandingan, dan performa pemain. Setelah eksplorasi sumber data, cakupan dipersempit menjadi Season 12-17 karena format franchise league pada rentang ini lebih stabil dan data antar season lebih konsisten untuk dimodelkan. Statistik performa pemain juga tidak jadi dimasukkan karena Liquipedia tidak menyediakan statistik performa pemain per match pada halaman MPL Indonesia; data statistik yang tersedia lebih mengarah ke statistik hero, sehingga tidak sesuai dengan rancangan awal berbasis performa pemain.

DBMS yang digunakan adalah MariaDB. Database relasional utama bernama `mpl_indonesia`, sedangkan bonus data warehouse menggunakan database `mpl_indonesia_dw`.

## Struktur Repository

```text
Data Scraping/
  src/       script scraping dan preprocessing
  data/      hasil scraping dalam format JSON

Data Storing/
  design/    ERD dan model relasional
  src/       schema, seed, loader, dumper, dan proof queries
  export/    hasil export database relasional
  screenshot/ bukti SELECT pada MariaDB

Data Warehouse/
  design/    diagram star schema
  src/       schema, loader, dumper, dan query analitik
  export/    hasil export data warehouse
  screenshot/ bukti query data warehouse

Query Optimasi/
  query_optimasi.sql
  screenshot/ bukti query sebelum dan sesudah optimasi
```

## Cara Menjalankan

Install dependency Python:

```bash
pip install -r requirements.txt
```

Menjalankan seluruh scraper:

```bash
cd "Data Scraping/src"
python main.py
```

Script `main.py` menjalankan scraper sesuai urutan dependensi: season, tim, award, roster, pengayaan role award, pemain, lalu match. Output akan tersimpan di `Data Scraping/data`.

Membuat dan mengisi database MariaDB:

```bash
python "Data Storing/src/load_db.py" --user root --password --disable-ssl
```

Export database relasional:

```bash
python "Data Storing/src/dump_db.py" --user root --password --disable-ssl
```

Menjalankan query bukti penyimpanan:

```bash
mariadb -u root -p mpl_indonesia < "Data Storing/src/proof_queries.sql"
```

Membuat dan mengisi data warehouse:

```bash
python "Data Warehouse/src/load_dw.py" --user root --password --disable-ssl
```

Export data warehouse:

```bash
python "Data Warehouse/src/dump_dw.py" --user root --password --disable-ssl
```

Menjalankan query analitik data warehouse:

```bash
mariadb -u root -p mpl_indonesia_dw < "Data Warehouse/src/analytics_queries.sql"
```

Menjalankan query optimasi:

```bash
mariadb -u root -p mpl_indonesia < "Query Optimasi/query_optimasi.sql"
```

## Struktur JSON

| File | Isi | Jumlah data |
| --- | --- | ---: |
| `seasons.json` | Informasi season, tanggal mulai/selesai, prize pool, lokasi, winner, runner-up | 6 |
| `teams.json` | Master tim dengan nama yang sudah dinormalisasi | 10 |
| `team_seasons.json` | Partisipasi tim per season, final rank, match wins/losses, game wins/losses | 54 |
| `rosters.json` | Pemain dan staff per tim per season, termasuk status roster dan role | 520 |
| `players.json` | Master person dari hasil normalisasi roster | 214 |
| `awards.json` | Award pemain per season, tim, dan role hasil normalisasi/pengayaan | 86 |
| `matches.json` | Hasil pertandingan regular season dan playoffs | 480 |

Beberapa preprocessing yang dilakukan:

- normalisasi nama tim, misalnya `Fnatic ONIC` menjadi `ONIC`, `RRQ Hoshi` menjadi `RRQ`, dan `Team Vitality` menjadi `Bigetron`;
- parsing `date_range` menjadi `start_date` dan `end_date`;
- parsing `prize_pool` menjadi angka `prize_pool_usd`;
- pemisahan lokasi season menjadi beberapa lokasi;
- parsing record seperti `12-4` menjadi kolom numerik wins/losses;
- normalisasi role pemain menjadi `EXP Laner`, `Gold Laner`, `Jungler`, `Mid Laner`, dan `Roamer`;
- pembersihan role `DNP` karena bukan role roster aktif.

## ERD dan Model Relasional

ERD konseptual:

![ERD](<Data Storing/design/MPL Database-ERD.png>)

Model relasional:

![Model Relasional](<Data Storing/design/MPL Database-Model Relasional.png>)

Entitas utama pada ERD adalah `season`, `team`, `person`, `match`, dan `award_type`. Relasi pentingnya adalah:

- `participates_in` antara `season` dan `team`, diterjemahkan menjadi tabel `team_season`;
- `listed_on_roster` antara `person`, `team`, dan `season`, diterjemahkan menjadi tabel `roster`;
- `contains` antara `season` dan `match`, diterjemahkan dengan foreign key `season_number` pada tabel `matches`;
- `plays_in` antara `team` dan `match`, diterjemahkan menjadi tabel `match_team`;
- `receives` antara entry roster dan award, diterjemahkan menjadi tabel `roster_award`.

Pada implementasi MariaDB, tabel `match` diberi nama `matches` agar tidak bentrok dengan reserved word. Atribut `location` pada season dipisahkan menjadi `season_location` karena satu season dapat berlangsung di lebih dari satu kota.

Constraint yang diimplementasikan meliputi primary key, foreign key, unique constraint, check constraint, dan trigger. Trigger digunakan untuk memastikan tim pada `match_team` memang berpartisipasi pada season pertandingan tersebut, satu match tidak memiliki lebih dari dua tim, dan award seperti Dream Team/First Team/Second Team hanya memiliki satu penerima untuk setiap role utama per season.

## Data Warehouse

Bonus data warehouse dibuat dengan pendekatan star schema.

![Data Warehouse](<Data Warehouse/design/MPL Database-Data Warehouse.png>)

Dimension table:

- `dim_season`
- `dim_team`
- `dim_person`
- `dim_award_type`
- `dim_role`
- `dim_match`

Fact table:

- `fact_team_season`, untuk analisis performa tim per season;
- `fact_team_match`, untuk analisis hasil pertandingan per tim;
- `fact_award`, untuk analisis distribusi award berdasarkan season, tim, person, dan role.

Contoh query analitik disediakan pada `Data Warehouse/src/analytics_queries.sql`.

## Query Optimasi

Bonus query optimasi disimpan pada `Query Optimasi/query_optimasi.sql`. File tersebut berisi tiga optimasi:

- ringkasan award per season dan tim;
- riwayat pertandingan sebuah tim pada season tertentu;
- pencarian roster utama berdasarkan season, tim, dan status roster.

Setiap query menampilkan `EXPLAIN` dan output sebelum dan sesudah indeks tambahan dibuat, sehingga hasil query dapat dibandingkan dengan rencana eksekusinya.

## Screenshot

Contoh bukti penyimpanan data pada MariaDB:

![Row Counts](<Data Storing/screenshot/01_table_row_counts.png>)

![Season 17 Standings](<Data Storing/screenshot/02_season17_team_standings.png>)

![Award Role Validation](<Data Storing/screenshot/06_team_award_role_validation.png>)

Contoh bukti data warehouse:

![DW Row Counts](<Data Warehouse/screenshot/01_dw_table_row_counts.png>)

![DW Team Match Summary](<Data Warehouse/screenshot/03_dw_team_match_summary.png>)

Contoh bukti query optimasi:

![Award Optimization](<Query Optimasi/screenshot/01_award_optimization.png>)

![Roster Optimization](<Query Optimasi/screenshot/04_roster_optimization.png>)

## Penggunaan AI

AI digunakan sebagai asisten diskusi dan review teknis selama pengerjaan, terutama untuk:

- membantu mengecek konsistensi hasil scraping dan normalisasi data;
- mendiskusikan rancangan ERD, model relasional, dan skema data warehouse;
- membantu menulis serta merapikan script SQL/Python;
- membantu mengecek dokumentasi, komentar, dan struktur repository.

Bagian yang tetap dikerjakan dan divalidasi oleh penulis meliputi pemilihan topik, pengecekan sumber data, pengambilan screenshot bukti, eksekusi MariaDB lokal, keputusan scope S12-S17, serta pengecekan akhir sebelum submission.

Refleksi penggunaan AI: bantuan AI paling berguna pada tahap review karena dapat menemukan inkonsistensi kecil, misalnya alias nama tim, role roster, dan constraint database. Namun hasilnya tetap perlu dicek manual terhadap data asli dan hasil query MariaDB, karena keputusan seperti pengurangan scope, pemilihan atribut yang disimpan, dan bukti screenshot tetap bergantung pada konteks tugas dan validasi langsung.

## Referensi

- Liquipedia MPL Indonesia: <https://liquipedia.net/mobilelegends/MPL_Indonesia>
- Halaman season Liquipedia MPL Indonesia Season 12-17
- Python `requests`
- BeautifulSoup (`beautifulsoup4`)
- MariaDB
