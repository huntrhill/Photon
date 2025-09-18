import os, psycopg2
from psycopg2.extras import RealDictCursor

def _conn():
    return psycopg2.connect(
        host=os.getenv("PGHOST","127.0.0.1"), port=int(os.getenv("PGPORT","5432")),
        dbname=os.getenv("PGDATABASE","photon"), user=os.getenv("PGUSER","postgres"),
        password=os.getenv("PGPASSWORD","postgres"), cursor_factory=RealDictCursor)

def get_player(pid:int):
    with _conn() as c, c.cursor() as cur:
        cur.execute("SELECT id,codename FROM players WHERE id=%s",(pid,))
        return cur.fetchone()

def add_player(pid:int, codename:str):
    with _conn() as c, c.cursor() as cur:
        cur.execute("INSERT INTO players(id,codename) VALUES (%s,%s) RETURNING id,codename",(pid,codename))
        return cur.fetchone()
