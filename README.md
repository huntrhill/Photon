Photon Laser Tag – Main Software (Debian)

What this is
A PyQt5 desktop app that runs on a Debian VM and coordinates a two-team (Red/Green) Photon game. It connects to a PostgreSQL database (photon) with a players table, plays synchronized MP3 music, and talks over UDP using 127.0.0.1 (configurable) with:

Send/broadcast: UDP 7500 (single integer = equipment id)

Receive: UDP 7501 (format txId:hitId or special codes)

Key behaviors

Splash screen (3s) with logo, then Player Entry screen

Operator enters player id → fetches codename from DB; if missing, you can add one (new row in players)

Prompt for equipment id (integer) → broadcast equipment id on UDP 7500

Up to 15 players per team; F5 or Start to continue; F12 or Clear wipes entries

30s pre-game warning (syncs MP3 countdown) then 6 min game timer

On game start (after countdown): broadcast 202

On game end: broadcast 221 three times

On data received (txId:hitId): broadcast hitId; if friendly fire, also broadcast txId

Base scores:

Receive 53 → “Red base scored” → if player is Green, award +100 and show base icon left of codename

Receive 43 → “Green base scored” → if player is Red, award +100 and show base icon

Scoring: +10 for tagging opponent; −10 for tagging same team; on friendly fire, both the tagger and the tagged lose 10

Game screen: live play-by-play feed, team totals, and per-player sorted scores; the leading team flashes

After game, remain on the game screen; button returns to Player Entry

1) Requirements

Debian 12+ VM (provided by instructor)

PostgreSQL running with a database named photon and a table players (existing)

Internet (to apt/pip once)

2) Install (automated)
git clone https://example.com/yourusername/photon-ltag.git
cd photon-ltag
chmod +x install.sh
./install.sh


This will:

Install system deps (python3-venv, python3-dev, libpq-dev, mpg123)

Create a Python venv, install pip packages from requirements.txt

3) Configure

Copy .env.example to .env and edit if needed:

# Network
PHOTON_BIND_ADDR=0.0.0.0   # UDP receive bind (allow any)
PHOTON_SEND_ADDR=127.0.0.1 # UDP send target
PHOTON_SEND_PORT=7500
PHOTON_RECV_PORT=7501

# Database (match your VM)
PGHOST=127.0.0.1
PGPORT=5432
PGDATABASE=photon
PGUSER=postgres
PGPASSWORD=postgres

4) Run
source .venv/bin/activate
python3 main.py

5) Operator flow

Splash (3s) → Entry screen

Enter Player ID → app queries players; if not found, supply a codename (app inserts it)

Enter Equipment ID (integer) → app broadcasts equipment id on UDP 7500

Repeat (max 15/team). F12 clears; F5 or Start begins

30s warning starts music + on-screen countdown → 202 is broadcast when game begins

Game (6:00): scores & play-by-play update on received UDP messages

Game end: broadcast 221 three times; UI stays on game screen; click Back to return to Entry

6) Assets

Put logo.jpg, baseicon.jpg, and MP3 tracks into photon/assets/.
The instructor’s repo includes logo.jpg, baseicon.jpg, and audio folders you can copy (see “Can I use the instructor repo?” below).

7) Uninstall

Remove the project folder and its .venv. No system services are installed.
