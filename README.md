# Photon Laser Tag System

Main software for running Photon laser tag matches.  
Written in **Python 3** with **PyQt5**, it connects to the provided **PostgreSQL** database, handles **UDP traffic** for scoring and events, plays synchronized **MP3 music**, and manages the operator UI for two teams: **Red** and **Green**.

---

## Features

- **Splash screen** (3s) with provided logo
- **Player entry screen**:
  - Enter **Player ID** → fetch codename from DB (`players` table)  
  - If not found → prompt codename and insert into DB  
  - Enter **Equipment ID** → immediately broadcast over UDP (port 7500)  
  - Assign to **Red** or **Green** team (max 15 players each)
- **Game play screen**:
  - **6-minute timer** with **30-second warning countdown**
  - **Live play-by-play feed**
  - **Cumulative team scores** and **individual scores** (sorted high → low)
  - **Scoring rules:**  
    - +10 for tagging opponent  
    - −10 for tagging same team (both tagger & tagged)  
    - Base scores:  
      - `53`: Red base scored → Green +100 (base icon shown)  
      - `43`: Green base scored → Red +100 (base icon shown)
  - High team score **flashes** during play
  - **Random MP3 track** plays during the game, synced to countdown
- **End of game**:
  - Broadcast code **221** three times
  - Game screen remains visible; operator can return to entry screen

---

## Assets

This project pulls required assets (logo, sounds, MP3s) from the instructor’s [photon-main](https://github.com/jstrother123/photon-main) repository.  
Local repo directories:
PhotonGame/assets/
├── images/ # logos, icons
├── tracks/ # MP3 background music
└── sfx/ # sound effects


---

## System Requirements

- **Debian 12+ VM** (provided by instructor)
- **PostgreSQL** with database `photon` and table `players` already installed
- Internet access for package installs

---

## Installation

Clone the repo into your Debian VM:

```bash
git clone https://github.com/huntrhill/Photon.git
cd Photon
chmod +x install.sh
./install.sh
```

The installer will:

- Create a Python virtual environment (.venv)

- Install dependencies from requirements.txt

- If PyQt5 fails (common on Debian VMs), it will automatically install Debian’s system python3-pyqt5 and rebuild the venv with --system-site-packages

- Validate that all modules import correctly (PyQt5, pygame, psycopg2, etc.)

---

## Running
```bash
source .venv/bin/activate
python3 main.py
```

---

## Team 

  GitHub	  |   Real Name	    |  Role
@huntrhill	|  Hunter Hill    |	Lead / UI – Entry
@member2	  |  Chance Pickett |	UI – Splash / Scoring
@dugku      |  Michael Purtle | Networking / Audio / UI – Game
@coaluh	    |  Cody Uhl	      | QA / Docs / Architecture

All team members used real names on GitHub or are cross-referenced above.
