import psycopg2, os
from psycopg2.extras import RealDictCursor

def _conn():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "127.0.0.1"),
        port=int(os.getenv("PGPORT", "5432")),
        dbname=os.getenv("PGDATABASE", "photon"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres"),
        cursor_factory=RealDictCursor,
    )

def get_player(player_id:int):
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, codename FROM players WHERE id=%s", (player_id,))
        return cur.fetchone()

def create_player(player_id:int, codename:str):
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO players(id, codename) VALUES (%s,%s) RETURNING id, codename",
                    (player_id, codename))
        return cur.fetchone()
