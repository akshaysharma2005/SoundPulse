# 🎵 Song Website Data Analysis

> An end-to-end analytical SQL case study and interactive web analytics dashboard for a music streaming platform.

---

## 📋 Overview

This project analyses two datasets from a music streaming website:

| Dataset | Records | Description |
|---|---|---|
| `events.csv` | 8,056 rows | Raw streaming event logs (user interactions, song plays, HTTP status) |
| `songs.csv` | 79 rows | Song catalog with artist metadata (geo-location, release year, duration) |

Using **PostgreSQL Analytical SQL** (window functions, CTEs, joins), we extracted actionable business intelligence across 6 key question areas. The project also includes a full **Interactive Web Dashboard** (Phase 2) for live exploration of the data.

---

## 🗂️ Project Structure

```
Song-Website-Data-Analysis/
├── Data/
│   ├── events.csv                            # 8,056 streaming event logs
│   └── songs.csv                             # 79-song artist catalog
│
├── Project Code/
│   ├── Creation of Events Table.txt          # DDL — CREATE TABLE EVENTS
│   ├── Creation of Songs Table.txt           # DDL — CREATE TABLE SONGS
│   ├── Insertion Data of Events Table.txt    # INSERT statements — EVENTS (8,056 rows)
│   ├── Insertion Data of Songs Table.sql     # INSERT statements — SONGS  (79 rows) ✅ NEW
│   ├── QUERY 1.sql   → QUERY 10.sql          # 10 analytical SQL queries (fixed & formatted) ✅
│   ├── Join Two Datasets With Artists Name.txt
│   ├── Join Two Datasets With Songs Name.txt
│   ├── Select all Events Data.txt
│   └── Select all Songs Data.txt
│
├── Important Note.sql                        # JOIN analysis & data disparity explanation ✅
├── Story_and_Conclusion.txt                  # Business case study story & conclusion ✅
├── Queries and Business Report.docx          # Original query output screenshots & report
├── Description/                              # Case study requirements
│   └── Analytical SQL Case Study2022.docx
├── Screen Shots/                             # Query result screenshots
├── dashboard/                                # Phase 2: Interactive Web Dashboard ✅ NEW
│   ├── app.py                                # Python Flask + SQLite backend API
│   └── index.html                            # Single-page analytics dashboard
└── README.md                                 # This file
```

---

## 🗄️ Database Schema

### EVENTS Table
Captures every user interaction on the platform.

| Column | Type | Description |
|---|---|---|
| `ARTIST_NAME` | VARCHAR(200) | Artist of the song played |
| `USER_AUTHENTICATION` | VARCHAR(200) | Authentication level |
| `USER_FIRST_NAME` | VARCHAR(200) | User first name |
| `USER_GENDER` | VARCHAR(5) | User gender (M/F) |
| `NO_ITEMS_IN_SESSION` | NUMERIC(10) | Items count in current session |
| `USER_LAST_NAME` | VARCHAR(200) | User last name |
| `SONG_LENGTH_IN_SECONDS` | NUMERIC(26,6) | Duration of the song in seconds |
| `SONG_LEVEL` | VARCHAR(200) | Subscription tier: `paid` or `free` |
| `USER_LOCATION` | VARCHAR(200) | User's city & state |
| `SONG_METHOD` | VARCHAR(200) | HTTP method (GET/PUT) |
| `SONG_PLAYED` | VARCHAR(200) | Page type: `NextSong`, `Home`, `Error`, etc. |
| `USER_REGISTRATION_TIME` | NUMERIC(26,6) | Registration timestamp (epoch ms) |
| `SESSION_ID` | NUMERIC(5) | Session identifier |
| `SONG_NAME` | VARCHAR(200) | Song title played |
| `SONG_STATUS` | NUMERIC(5) | HTTP status code (200, 404, 307) |
| `TIME_IN_SECONDS` | NUMERIC(26,6) | Event timestamp (epoch ms) |
| `USER_AGENT` | VARCHAR(400) | Browser/OS user-agent string |
| `USER_ID` | NUMERIC(10) | Unique user identifier |

### SONGS Table
Curated catalog of 79 songs with artist metadata.

| Column | Type | Description |
|---|---|---|
| `ARTIST_ID` | VARCHAR(100) | Unique artist identifier |
| `ARTIST_LATITUDE` | NUMERIC(20,6) | Artist location — latitude |
| `ARTIST_LOCATION` | VARCHAR(100) | Artist city/country |
| `ARTIST_LONGTUDE` | NUMERIC(20,6) | Artist location — longitude |
| `ARTIST_NAME` | VARCHAR(100) | Artist name |
| `SONG_DURATION_IN_SECONDS` | NUMERIC(20,6) | Song duration |
| `ARTIST_NUM_OF_SONGS` | NUMERIC(5) | Number of songs by this artist in catalog |
| `SONG_ID` | VARCHAR(100) | Unique song identifier |
| `SONG_NAME` | VARCHAR(100) | Song title |
| `SONG_REALASED_YEAR` | NUMERIC(5) | Song release year |

---

## 📊 Query Catalog

All 10 queries use PostgreSQL **Window Functions** (`DENSE_RANK`, `COUNT OVER PARTITION BY`, `SUM OVER`, `FIRST_VALUE`). Fixed versions are saved as `.sql` files.

| Query | Business Question | Key Technique | Bug Fixed? |
|---|---|---|---|
| **QUERY 1** | Which artists attract the most unique listeners? | `COUNT OVER PARTITION BY`, `LEFT JOIN` | ✅ INNER → LEFT JOIN |
| **QUERY 2** | Which songs are played most often? | `COUNT OVER PARTITION BY`, `LEFT JOIN`, `DISTINCT` | ✅ INNER → LEFT JOIN, added DISTINCT |
| **QUERY 3** | What are the most popular songs with tier and rank? | `DENSE_RANK`, `COUNT OVER PARTITION BY` | — |
| **QUERY 4** | How do songs rank within each individual session? | `DENSE_RANK OVER PARTITION BY SESSION_ID` | — |
| **QUERY 5** | Which artists have produced the most distinct songs? | `COUNT DISTINCT`, `DENSE_RANK` | ✅ Removed SONG_NAME grain, filtered empty strings |
| **QUERY 6** | Who are the most active power users? | `COUNT GROUP BY`, `DENSE_RANK DESC` | ✅ Fixed ASC→DESC rank, removed duplicate columns |
| **QUERY 7** | What are the longest and shortest songs per session? | `FIRST_VALUE OVER PARTITION BY` | — |
| **QUERY 8** | What is the true HTTP success rate per user? | `COUNT CASE WHEN`, `CAST AS FLOAT` | ✅ Removed `NextSong` filter (was causing 100% rate) |
| **QUERY 9** | What is each user's paid vs. free listening ratio? | `COUNT CASE WHEN SONG_LEVEL`, window ratios | — |
| **QUERY 10** | Who spends the most total time on the platform? | `SUM OVER PARTITION BY`, `DENSE_RANK` | ✅ Added `AS USER_RANK` alias |

---

## ⚠️ Critical JOIN Note

> See [`Important Note.sql`](Important%20Note.sql) for the full analysis.

The SONGS catalog (79 rows) and EVENTS log (8,056 rows) have **very low overlap** — only ~11 artist names match between the two tables. An `INNER JOIN` silently discards 99.7% of event data.

**Always use `LEFT JOIN` with EVENTS as the primary table** when enriching event data with catalog metadata.

| Join Type | Result Rows | Use Case |
|---|---|---|
| `INNER JOIN` | ~22 rows | ❌ Loses 99.7% of data |
| `LEFT JOIN` | ~3,200 rows | ✅ Recommended — all events kept |
| `RIGHT JOIN` | 79 rows | Catalog-centric — find unstreamed songs |
| `FULL OUTER JOIN` | ~3,200 rows | Full transparency diagnostic |

---

## 💡 Key Business Insights

1. **Hit Song Concentration**: A small fraction of songs account for the majority of plays — strong "long tail" dynamics.
2. **Power User Segment**: Top 10% of users by song count drive outsized platform engagement.
3. **Hidden Platform Errors**: HTTP 404 and 307 errors were invisible in original Query 8 due to a `NextSong` filter — fixed in the corrected version.
4. **Monetization Bimodal Split**: Users are either predominantly free or predominantly paid — very few mixed. High-activity free users are prime conversion targets.
5. **Catalog Expansion Needed**: The 79-song catalog is too small to represent real user listening behavior. Expanding via a music metadata API is the top infrastructure priority.

---

## 🚀 Running the Interactive Dashboard (Phase 2)

### Requirements
```bash
pip install flask pandas
```

### Start the Backend
```bash
cd dashboard
python app.py
```

### Open the Dashboard
Navigate to **http://localhost:5050** in your browser.

### Dashboard Features
- 📊 **KPI Cards** — Total Songs, Artists, Users, Listening Hours, Paid Ratio, Success Rate
- 🔍 **Live Search** — Instant search across all songs, artists, and users
- 🎵 **Song Inspector** — Click any song to see all listeners sorted by play count, tier, location
- 📈 **Interactive Charts** — Top Artists, Top Songs, Paid vs Free distribution, Error rates
- 🔬 **SQL Query Sandbox** — View and explore all 10 analytical queries with descriptions

---

## 📁 Related Documents

- [`Story_and_Conclusion.txt`](Story_and_Conclusion.txt) — Full business narrative and recommendations
- [`Important Note.sql`](Important%20Note.sql) — JOIN strategy analysis
- [`Queries and Business Report.docx`](Queries%20and%20Business%20Report.docx) — Original report with screenshots
- [`Description/Analytical SQL Case Study2022.docx`](Description/Analytical%20SQL%20Case%20Study2022.docx) — Original case study brief

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Database | PostgreSQL (analytical SQL, window functions) |
| Backend | Python 3, Flask, SQLite (in-memory), Pandas |
| Frontend | HTML5, Vanilla CSS, JavaScript, Chart.js |
| Data | CSV → SQL INSERT pipeline |
