import psycopg2
from psycopg2.extras import RealDictCursor
from .config import PG

def _conn():
    return psycopg2.connect(cursor_factory=RealDictCursor, **PG)

def get_or_create_player(player_id: int, codename: str|None):
    """
    If player_id exists: return row & ignore codename.
    Else: require codename and insert.
    Assumes table `players(id INT PRIMARY KEY, codename TEXT, team TEXT)`
    (Do NOT alter schema; only insert/delete as instructed.)
    """
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, codename, team FROM players WHERE id=%s", (player_id,))
        row = cur.fetchone()
        if row:
            return row
        if not codename:
            raise ValueError("Codename required for new player.")
        cur.execute("INSERT INTO players(id, codename) VALUES (%s,%s) RETURNING id, codename", (player_id, codename))
        return cur.fetchone()
