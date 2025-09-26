import os, psycopg2
from psycopg2.extras import RealDictCursor

def _conn():
	connection_params = {
		'dbname': 'photon',
		'user': 'student',
		#'password': 'student',
		#'host': 'localhost',
		#'port': '5432'
	}
	con = psycopg2.connect(**connection_params)
	return con

def get_player(pid:int):
	with _conn() as c, c.cursor() as cur:
		cur.execute("SELECT id,codename FROM players WHERE id=%s",(pid,))
		return cur.fetchone()

def add_player(pid:int, codename:str):
	with _conn() as c, c.cursor() as cur:
		cur.execute("INSERT INTO players(id,codename) VALUES (%s,%s) RETURNING id,codename",(pid,codename))
		return cur.fetchone()
