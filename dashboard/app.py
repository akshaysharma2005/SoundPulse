"""
SoundPulse — Music Streaming Analytics Dashboard Backend
Flask + SQLite in-memory data service
Loads events.csv and songs.csv into SQLite for fast API querying
Compatible with gunicorn (Render deployment) and local development
"""

import os
import csv
import sqlite3
import json
from flask import Flask, jsonify, request
from flask.wrappers import Response

app = Flask(__name__, static_folder='.', static_url_path='')

# ─────────────────────────────────────────────
# DATA LOADING INTO SQLITE (in-memory)
# ─────────────────────────────────────────────
DB_PATH = ':memory:'

def get_db():
    """Create and return a new in-memory SQLite connection with data loaded."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Global in-memory connection (kept alive for app lifetime)
_conn = None

def init_db():
    global _conn
    _conn = sqlite3.connect(':memory:', check_same_thread=False)
    _conn.row_factory = sqlite3.Row

    # Resolve the Data/ folder relative to this file's location.
    # Works whether the app is run from project root or from dashboard/
    this_dir = os.path.dirname(os.path.abspath(__file__))
    # If Data/ is a sibling of this file (i.e. run from root)
    if os.path.isdir(os.path.join(this_dir, 'Data')):
        base = this_dir
    else:
        # Data/ is one level up (dashboard/app.py → project root)
        base = os.path.dirname(this_dir)

    cur = _conn.cursor()

    # ── CREATE TABLES ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            artist       TEXT,
            auth         TEXT,
            firstName    TEXT,
            gender       TEXT,
            itemInSession INTEGER,
            lastName     TEXT,
            length       REAL,
            level        TEXT,
            location     TEXT,
            method       TEXT,
            page         TEXT,
            registration REAL,
            sessionId    INTEGER,
            song         TEXT,
            status       INTEGER,
            ts           REAL,
            userAgent    TEXT,
            userId       INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            artist_id       TEXT,
            artist_latitude REAL,
            artist_location TEXT,
            artist_longitude REAL,
            artist_name     TEXT,
            duration        REAL,
            num_songs       INTEGER,
            song_id         TEXT,
            title           TEXT,
            year            INTEGER
        )
    """)

    # ── LOAD events.csv ──
    events_path = os.path.join(base, 'Data', 'events.csv')
    with open(events_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute("""
                INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                row['artist'] or None,
                row['auth'] or None,
                row['firstName'] or None,
                row['gender'] or None,
                int(row['itemInSession']) if row['itemInSession'] else None,
                row['lastName'] or None,
                float(row['length']) if row['length'] else None,
                row['level'] or None,
                row['location'] or None,
                row['method'] or None,
                row['page'] or None,
                float(row['registration']) if row['registration'] else None,
                int(row['sessionId']) if row['sessionId'] else None,
                row['song'] or None,
                int(row['status']) if row['status'] else None,
                float(row['ts']) if row['ts'] else None,
                row['userAgent'] or None,
                int(float(row['userId'])) if row['userId'] else None,
            ))

    # ── LOAD songs.csv ──
    songs_path = os.path.join(base, 'Data', 'songs.csv')
    with open(songs_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute("""
                INSERT INTO songs VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                row['artist_id'] or None,
                float(row['artist_latitude']) if row['artist_latitude'] else None,
                row['artist_location'] or None,
                float(row['artist_longitude']) if row['artist_longitude'] else None,
                row['artist_name'] or None,
                float(row['duration']) if row['duration'] else None,
                int(row['num_songs']) if row['num_songs'] else None,
                row['song_id'] or None,
                row['title'] or None,
                int(row['year']) if row['year'] and row['year'] != '0' else None,
            ))

    _conn.commit()
    print(f"✅ Database loaded: events={cur.execute('SELECT COUNT(*) FROM events').fetchone()[0]}, songs={cur.execute('SELECT COUNT(*) FROM songs').fetchone()[0]}")

# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────
def rows_to_list(cursor_result):
    cols = [d[0] for d in cursor_result.description]
    return [dict(zip(cols, row)) for row in cursor_result.fetchall()]

def jsonify_rows(rows):
    return Response(json.dumps(rows, default=str), mimetype='application/json')

# ─────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/kpis')
def kpis():
    cur = _conn.cursor()
    total_songs    = cur.execute("SELECT COUNT(DISTINCT song) FROM events WHERE page='NextSong' AND song IS NOT NULL").fetchone()[0]
    total_artists  = cur.execute("SELECT COUNT(DISTINCT artist) FROM events WHERE page='NextSong' AND artist IS NOT NULL AND artist != ''").fetchone()[0]
    total_users    = cur.execute("SELECT COUNT(DISTINCT userId) FROM events WHERE userId IS NOT NULL").fetchone()[0]
    listening_hrs  = cur.execute("SELECT ROUND(SUM(length)/3600.0, 1) FROM events WHERE page='NextSong' AND length IS NOT NULL").fetchone()[0]
    paid_streams   = cur.execute("SELECT COUNT(*) FROM events WHERE page='NextSong' AND level='paid'").fetchone()[0]
    total_streams  = cur.execute("SELECT COUNT(*) FROM events WHERE page='NextSong'").fetchone()[0]
    paid_ratio     = round(paid_streams / total_streams * 100, 1) if total_streams else 0
    success_count  = cur.execute("SELECT COUNT(*) FROM events WHERE status=200").fetchone()[0]
    total_requests = cur.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    success_rate   = round(success_count / total_requests * 100, 1) if total_requests else 0

    return jsonify({
        'total_songs':    total_songs,
        'total_artists':  total_artists,
        'total_users':    total_users,
        'listening_hours': listening_hrs,
        'paid_ratio':     paid_ratio,
        'success_rate':   success_rate,
        'total_streams':  total_streams,
        'total_requests': total_requests,
    })

@app.route('/api/top_songs')
def top_songs():
    cur = _conn.cursor()
    limit = request.args.get('limit', 10, type=int)
    rows = cur.execute("""
        SELECT song AS name, artist, level, COUNT(userId) AS play_count
        FROM events
        WHERE page='NextSong' AND song IS NOT NULL AND song != ''
        GROUP BY song
        ORDER BY play_count DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return jsonify_rows([dict(r) for r in rows])

@app.route('/api/top_artists')
def top_artists():
    cur = _conn.cursor()
    limit = request.args.get('limit', 10, type=int)
    rows = cur.execute("""
        SELECT artist AS name, COUNT(DISTINCT userId) AS listener_count,
               COUNT(DISTINCT song) AS unique_songs
        FROM events
        WHERE page='NextSong' AND artist IS NOT NULL AND artist != ''
        GROUP BY artist
        ORDER BY listener_count DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return jsonify_rows([dict(r) for r in rows])

@app.route('/api/monetization')
def monetization():
    cur = _conn.cursor()
    rows = cur.execute("""
        SELECT level, COUNT(*) AS stream_count
        FROM events
        WHERE page='NextSong'
        GROUP BY level
    """).fetchall()
    return jsonify_rows([dict(r) for r in rows])

@app.route('/api/status_distribution')
def status_distribution():
    cur = _conn.cursor()
    rows = cur.execute("""
        SELECT status, COUNT(*) AS count,
               ROUND(COUNT(*)*100.0 / (SELECT COUNT(*) FROM events), 2) AS pct
        FROM events
        GROUP BY status
        ORDER BY count DESC
    """).fetchall()
    return jsonify_rows([dict(r) for r in rows])

@app.route('/api/power_users')
def power_users():
    cur = _conn.cursor()
    limit = request.args.get('limit', 15, type=int)
    rows = cur.execute("""
        SELECT userId, firstName, lastName, gender, location, level,
               COUNT(song) AS songs_played,
               ROUND(SUM(length)/3600.0, 2) AS hours_listened
        FROM events
        WHERE page='NextSong' AND userId IS NOT NULL AND song IS NOT NULL
        GROUP BY userId
        ORDER BY songs_played DESC
        LIMIT ?
    """, (limit,)).fetchall()
    result = [dict(r) for r in rows]
    for i, r in enumerate(result):
        r['rank'] = i + 1
    return jsonify_rows(result)

@app.route('/api/song_listeners')
def song_listeners():
    song_name = request.args.get('song', '')
    if not song_name:
        return jsonify({'error': 'song parameter required'}), 400
    sort = request.args.get('sort', 'play_count')  # play_count | ts | level | location
    cur = _conn.cursor()

    order_map = {
        'play_count': 'play_count DESC',
        'ts':         'last_listen DESC',
        'level':      'level DESC, play_count DESC',
        'location':   'location ASC',
    }
    order_clause = order_map.get(sort, 'play_count DESC')

    rows = cur.execute(f"""
        SELECT userId, firstName, lastName, gender, location, level,
               COUNT(*) AS play_count,
               MAX(ts) AS last_listen
        FROM events
        WHERE page='NextSong' AND song = ? AND userId IS NOT NULL
        GROUP BY userId
        ORDER BY {order_clause}
    """, (song_name,)).fetchall()
    return jsonify_rows([dict(r) for r in rows])

@app.route('/api/search')
def search():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'songs': [], 'artists': [], 'users': []})
    cur = _conn.cursor()
    like = f'%{q}%'

    songs = cur.execute("""
        SELECT DISTINCT song AS name, artist, COUNT(*) AS plays
        FROM events
        WHERE page='NextSong' AND song LIKE ? AND song IS NOT NULL
        GROUP BY song ORDER BY plays DESC LIMIT 8
    """, (like,)).fetchall()

    artists = cur.execute("""
        SELECT DISTINCT artist AS name, COUNT(DISTINCT userId) AS listeners
        FROM events
        WHERE page='NextSong' AND artist LIKE ? AND artist IS NOT NULL AND artist != ''
        GROUP BY artist ORDER BY listeners DESC LIMIT 8
    """, (like,)).fetchall()

    users = cur.execute("""
        SELECT DISTINCT userId, firstName, lastName, location, level,
               COUNT(song) AS songs_played
        FROM events
        WHERE (firstName LIKE ? OR lastName LIKE ?) AND userId IS NOT NULL
        GROUP BY userId ORDER BY songs_played DESC LIMIT 8
    """, (like, like)).fetchall()

    return jsonify({
        'songs':   [dict(r) for r in songs],
        'artists': [dict(r) for r in artists],
        'users':   [dict(r) for r in users],
    })

@app.route('/api/queries')
def get_queries():
    queries = [
        {
            "id": 1,
            "title": "Artist Popularity by Listener Count",
            "description": "Ranks artists by the number of unique users who have listened to their songs. Uses LEFT JOIN with the catalog for geographic enrichment.",
            "business_question": "Which artists attract the broadest audience on the platform?",
            "bug_fixed": "Changed INNER JOIN → LEFT JOIN to prevent 99.7% data loss",
            "sql": """SELECT DISTINCT
    E.artist AS ARTIST_NAME,
    S.artist_id AS ARTIST_ID,
    S.artist_location AS ARTIST_LOCATION,
    COUNT(E.userId) OVER (PARTITION BY E.artist) AS USERS_NUMBER
FROM events E
LEFT JOIN songs S ON E.artist = S.artist_name
ORDER BY USERS_NUMBER DESC;"""
        },
        {
            "id": 2,
            "title": "Most Played Songs",
            "description": "Shows which songs are streamed most often, enriched with catalog metadata where available. Uses LEFT JOIN and DISTINCT to eliminate duplicates.",
            "business_question": "Which songs should we promote and recommend to maximize streams?",
            "bug_fixed": "INNER JOIN → LEFT JOIN; added DISTINCT to eliminate 1-to-many duplicate rows",
            "sql": """SELECT DISTINCT
    E.song AS SONG_NAME,
    S.song_id AS SONG_ID,
    S.artist_id AS ARTIST_ID,
    E.artist AS ARTIST_NAME,
    E.length AS SONG_LENGTH_IN_SECONDS,
    COUNT(E.userId) OVER (PARTITION BY E.song) AS USERS_NUMBER
FROM events E
LEFT JOIN songs S ON E.song = S.title
WHERE E.page = 'NextSong' AND E.song IS NOT NULL
ORDER BY USERS_NUMBER DESC;"""
        },
        {
            "id": 3,
            "title": "Top Songs with Tier & Global Rank",
            "description": "Ranks the most-played songs globally, also showing their subscription tier (paid/free) and artist name.",
            "business_question": "What is the overall popularity ranking of songs across all paid and free tiers?",
            "bug_fixed": None,
            "sql": """SELECT *, DENSE_RANK() OVER (ORDER BY USERS_NUMBER DESC) AS SONG_RANK
FROM (
    SELECT DISTINCT
        song AS SONG_NAME,
        artist AS ARTIST_NAME,
        level AS SONG_LEVEL,
        COUNT(userId) OVER (PARTITION BY song) AS USERS_NUMBER
    FROM events
    WHERE page = 'NextSong'
) SUB_QUERY_1
WHERE SONG_NAME IS NOT NULL;"""
        },
        {
            "id": 4,
            "title": "Song Rank Within Each Session",
            "description": "Ranks songs by how many users played them within each specific session, revealing session-level hit songs.",
            "business_question": "Which songs dominate individual listening sessions vs. the global chart?",
            "bug_fixed": None,
            "sql": """SELECT * FROM (
    SELECT DISTINCT
        sessionId AS SESSION_ID,
        song AS SONG_NAME,
        USERS_NUMBER,
        artist AS ARTIST_NAME,
        level AS SONG_LEVEL,
        DENSE_RANK() OVER (PARTITION BY sessionId ORDER BY USERS_NUMBER DESC) AS SONG_RANK
    FROM (
        SELECT sessionId, song,
               COUNT(userId) OVER (PARTITION BY sessionId, song) AS USERS_NUMBER,
               artist, level
        FROM events
        WHERE song IS NOT NULL AND page = 'NextSong'
    ) SUB_QUERY
) SUB_QUERY_2
GROUP BY SESSION_ID, SONG_NAME, SONG_LEVEL, USERS_NUMBER, ARTIST_NAME, SONG_RANK
ORDER BY SESSION_ID, SONG_RANK;"""
        },
        {
            "id": 5,
            "title": "Artist Ranking by Song Variety",
            "description": "Ranks artists by the number of distinct songs played, showing which artists offer the most variety to listeners.",
            "business_question": "Which artists have the deepest catalogs actively being streamed?",
            "bug_fixed": "Removed SONG_NAME from grain (caused 5,296 duplicates); filtered empty artist strings",
            "sql": """SELECT
    artist AS ARTIST_NAME,
    SONGS_NUMBER,
    DENSE_RANK() OVER (ORDER BY SONGS_NUMBER DESC) AS ARTIST_RANK
FROM (
    SELECT artist,
           COUNT(DISTINCT song) AS SONGS_NUMBER
    FROM events
    WHERE artist IS NOT NULL AND artist != ''
      AND song IS NOT NULL AND page = 'NextSong'
    GROUP BY artist
) SUB_QUERY
ORDER BY ARTIST_RANK;"""
        },
        {
            "id": 6,
            "title": "Power User Leaderboard",
            "description": "Ranks users by total number of songs played across all sessions. The most active user ranks #1.",
            "business_question": "Who are our super-users and what is their engagement level?",
            "bug_fixed": "Fixed ascending rank bug → DESC; removed SESSION_ID and SONG_NAME that caused 6,786 duplicate rows",
            "sql": """SELECT
    USER_RANK, userId AS USER_ID,
    firstName AS USER_FIRST_NAME,
    lastName AS USER_LAST_NAME,
    gender AS USER_GENDER,
    SONGS_NUMBER
FROM (
    SELECT userId, firstName, lastName, gender,
           COUNT(song) AS SONGS_NUMBER,
           DENSE_RANK() OVER (ORDER BY COUNT(song) DESC) AS USER_RANK
    FROM events
    WHERE song IS NOT NULL AND page = 'NextSong'
    GROUP BY userId, firstName, lastName, gender
) SUB_QUERY
ORDER BY USER_RANK;"""
        },
        {
            "id": 7,
            "title": "Longest & Shortest Songs Per Session",
            "description": "For every session, shows which song was the longest and which was the shortest using FIRST_VALUE window function.",
            "business_question": "Do users tend to skip short songs or listen through long tracks in a given session?",
            "bug_fixed": None,
            "sql": """SELECT
    song AS SONG_NAME, artist AS ARTIST_NAME, sessionId AS SESSION_ID,
    length AS SONG_LENGTH_IN_SECONDS, userId AS USER_ID,
    FIRST_VALUE(song) OVER (PARTITION BY sessionId ORDER BY length DESC) AS LONGEST_SONG,
    FIRST_VALUE(song) OVER (PARTITION BY sessionId ORDER BY length ASC)  AS SHORTEST_SONG
FROM events
WHERE song IS NOT NULL AND page = 'NextSong'
ORDER BY SESSION_ID;"""
        },
        {
            "id": 8,
            "title": "Platform Reliability — True Success Rate Per User",
            "description": "Measures the true HTTP success rate (200 OK) for each user across ALL platform interactions, including 404 errors and 307 redirects.",
            "business_question": "Are some users experiencing significantly more errors than others?",
            "bug_fixed": "Removed 'NextSong' filter — it caused 100% success rate for all users by excluding 404/307 events",
            "sql": """SELECT DISTINCT
    userId AS USER_ID, firstName AS USER_FIRST_NAME, lastName AS USER_LAST_NAME,
    NUMBER_OF_REQUESTS, SUCCESSFUL_REQUESTS,
    CAST(SUCCESSFUL_REQUESTS AS FLOAT) / NUMBER_OF_REQUESTS AS SUCCESS_PERCENTAGE
FROM (
    SELECT userId, firstName, lastName,
           COUNT(userId) OVER (PARTITION BY userId) AS NUMBER_OF_REQUESTS,
           COUNT(CASE WHEN status = 200 THEN 1 END) OVER (PARTITION BY userId) AS SUCCESSFUL_REQUESTS
    FROM events
    WHERE userId IS NOT NULL
) SUB_QUERY
ORDER BY SUCCESS_PERCENTAGE ASC, USER_ID;"""
        },
        {
            "id": 9,
            "title": "Monetization Profile Per User",
            "description": "Shows each user's split between paid and free song streams, and their paid listening percentage.",
            "business_question": "Which free users are most active and most likely to convert to paid subscriptions?",
            "bug_fixed": None,
            "sql": """SELECT
    userId AS USER_ID, firstName AS USER_FIRST_NAME, lastName AS USER_LAST_NAME,
    PAID_SONGS_NUMBER, FREE_SONGS_NUMBER,
    CAST(PAID_SONGS_NUMBER AS FLOAT) / (PAID_SONGS_NUMBER + FREE_SONGS_NUMBER) AS PAID_SONGS_PERCENTAGE
FROM (
    SELECT DISTINCT userId, firstName, lastName,
           COUNT(CASE level WHEN 'paid' THEN 1 END) OVER (PARTITION BY userId) AS PAID_SONGS_NUMBER,
           COUNT(CASE level WHEN 'free' THEN 1 END) OVER (PARTITION BY userId) AS FREE_SONGS_NUMBER
    FROM events
    WHERE song IS NOT NULL AND page = 'NextSong'
) SUB_QUERY
ORDER BY USER_ID;"""
        },
        {
            "id": 10,
            "title": "Total Platform Time Per User",
            "description": "Ranks users by total seconds of music listened to across all sessions. Identifies the highest-value listeners.",
            "business_question": "Who spends the most time on our platform and contributes most to streaming hours?",
            "bug_fixed": "Added AS USER_RANK alias to DENSE_RANK() (was previously an unnamed column)",
            "sql": """SELECT
    userId AS USER_ID,
    DENSE_RANK() OVER (ORDER BY USER_DURATION_IN_SECONDS DESC) AS USER_RANK,
    firstName AS USER_FIRST_NAME, lastName AS USER_LAST_NAME,
    USER_DURATION_IN_SECONDS
FROM (
    SELECT DISTINCT userId, firstName, lastName,
           SUM(length) OVER (PARTITION BY userId) AS USER_DURATION_IN_SECONDS
    FROM events
    WHERE song IS NOT NULL AND page = 'NextSong'
) SUB_QUERY
ORDER BY USER_RANK;"""
        },
    ]
    return jsonify(queries)

@app.route('/api/run_query/<int:query_id>')
def run_query(query_id):
    """Run one of the pre-defined analytical queries against the SQLite data."""
    cur = _conn.cursor()

    query_map = {
        1: """SELECT DISTINCT E.artist AS ARTIST_NAME, S.artist_location AS ARTIST_LOCATION,
                     COUNT(E.userId) OVER (PARTITION BY E.artist) AS USERS_NUMBER
              FROM events E LEFT JOIN songs S ON E.artist = S.artist_name
              ORDER BY USERS_NUMBER DESC LIMIT 20""",
        2: """SELECT DISTINCT E.song AS SONG_NAME, E.artist AS ARTIST_NAME, E.length AS LENGTH,
                     COUNT(E.userId) OVER (PARTITION BY E.song) AS USERS_NUMBER
              FROM events E LEFT JOIN songs S ON E.song = S.title
              WHERE E.page = 'NextSong' AND E.song IS NOT NULL ORDER BY USERS_NUMBER DESC LIMIT 20""",
        3: """SELECT DISTINCT song AS SONG_NAME, artist AS ARTIST_NAME, level AS SONG_LEVEL,
                     COUNT(userId) OVER (PARTITION BY song) AS USERS_NUMBER,
                     DENSE_RANK() OVER (ORDER BY COUNT(userId) OVER (PARTITION BY song) DESC) AS SONG_RANK
              FROM events WHERE page='NextSong' AND song IS NOT NULL
              ORDER BY SONG_RANK LIMIT 20""",
        4: """SELECT DISTINCT sessionId AS SESSION_ID, song AS SONG_NAME, artist, level,
                     COUNT(userId) OVER (PARTITION BY sessionId, song) AS USERS_NUMBER,
                     DENSE_RANK() OVER (PARTITION BY sessionId ORDER BY COUNT(userId) OVER (PARTITION BY sessionId, song) DESC) AS SONG_RANK
              FROM events WHERE song IS NOT NULL AND page='NextSong' ORDER BY SESSION_ID, SONG_RANK LIMIT 20""",
        5: """SELECT artist AS ARTIST_NAME, COUNT(DISTINCT song) AS SONGS_NUMBER,
                     DENSE_RANK() OVER (ORDER BY COUNT(DISTINCT song) DESC) AS ARTIST_RANK
              FROM events WHERE artist IS NOT NULL AND artist!='' AND song IS NOT NULL AND page='NextSong'
              GROUP BY artist ORDER BY ARTIST_RANK LIMIT 20""",
        6: """SELECT userId AS USER_ID, firstName, lastName, gender, COUNT(song) AS SONGS_NUMBER,
                     DENSE_RANK() OVER (ORDER BY COUNT(song) DESC) AS USER_RANK
              FROM events WHERE song IS NOT NULL AND page='NextSong'
              GROUP BY userId, firstName, lastName, gender ORDER BY USER_RANK LIMIT 20""",
        7: """SELECT song, artist, sessionId, length,
                     FIRST_VALUE(song) OVER (PARTITION BY sessionId ORDER BY length DESC) AS LONGEST_SONG,
                     FIRST_VALUE(song) OVER (PARTITION BY sessionId ORDER BY length ASC) AS SHORTEST_SONG
              FROM events WHERE song IS NOT NULL AND page='NextSong' ORDER BY sessionId LIMIT 20""",
        8: """SELECT DISTINCT userId, firstName, lastName,
                     COUNT(userId) OVER (PARTITION BY userId) AS TOTAL_REQUESTS,
                     COUNT(CASE WHEN status=200 THEN 1 END) OVER (PARTITION BY userId) AS OK_REQUESTS,
                     ROUND(CAST(COUNT(CASE WHEN status=200 THEN 1 END) OVER (PARTITION BY userId) AS FLOAT)
                           / COUNT(userId) OVER (PARTITION BY userId) * 100, 1) AS SUCCESS_PCT
              FROM events WHERE userId IS NOT NULL ORDER BY SUCCESS_PCT ASC LIMIT 20""",
        9: """SELECT DISTINCT userId, firstName, lastName,
                     COUNT(CASE level WHEN 'paid' THEN 1 END) OVER (PARTITION BY userId) AS PAID,
                     COUNT(CASE level WHEN 'free' THEN 1 END) OVER (PARTITION BY userId) AS FREE,
                     ROUND(CAST(COUNT(CASE level WHEN 'paid' THEN 1 END) OVER (PARTITION BY userId) AS FLOAT)
                           / COUNT(song) OVER (PARTITION BY userId) * 100, 1) AS PAID_PCT
              FROM events WHERE song IS NOT NULL AND page='NextSong' ORDER BY userId LIMIT 20""",
        10: """SELECT DISTINCT userId, firstName, lastName,
                      ROUND(SUM(length) OVER (PARTITION BY userId)/60.0, 1) AS TOTAL_MINUTES,
                      DENSE_RANK() OVER (ORDER BY SUM(length) OVER (PARTITION BY userId) DESC) AS USER_RANK
               FROM events WHERE song IS NOT NULL AND page='NextSong' ORDER BY USER_RANK LIMIT 20""",
    }

    if query_id not in query_map:
        return jsonify({'error': 'Query not found'}), 404

    try:
        result = cur.execute(query_map[query_id])
        cols = [d[0] for d in result.description]
        rows = [dict(zip(cols, row)) for row in result.fetchall()]
        return jsonify({'columns': cols, 'rows': rows})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────────
# STARTUP
# init_db() is called at module load time so that gunicorn workers
# (used in production on Render) also get the database initialised.
# ─────────────────────────────────────────────
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print(f"🎵 SoundPulse Analytics Dashboard running at http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
