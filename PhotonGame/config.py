import os
from dotenv import load_dotenv
load_dotenv()

SEND_ADDR  = os.getenv("PHOTON_SEND_ADDR", "127.0.0.1")
SEND_PORT  = int(os.getenv("PHOTON_SEND_PORT", "7500"))
RECV_ADDR  = os.getenv("PHOTON_BIND_ADDR", "0.0.0.0")
RECV_PORT  = int(os.getenv("PHOTON_RECV_PORT", "7501"))

PG = dict(
    host=os.getenv("PGHOST", "127.0.0.1"),
    port=int(os.getenv("PGPORT", "5432")),
    dbname=os.getenv("PGDATABASE", "photon"),
    user=os.getenv("PGUSER", "postgres"),
    password=os.getenv("PGPASSWORD", "postgres"),
)
