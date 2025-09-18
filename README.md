# Photon Laser Tag System

Main software for running Photon laser tag matches.  
Written in **Python 3** with **PyQt5**, it connects to the provided **PostgreSQL** database, handles **UDP traffic** for scoring and events, plays synchronized **MP3 music**, and manages the operator UI for two teams: **Red** and **Green**.

---

## ✨ Features

- Splash screen (3s) with provided logo
- Player entry screen:
  - Enter **Player ID** → fetch codename from DB (`players` table)  
  - If not found → prompt codename and insert into DB  
  - Enter **Equipment ID** → immediately broadcast over UDP (7500)
  - Assign to **Red** or **Green** team (max 15 per team)
- Game play screen:
  - **6-minute timer** with **30-second warning** countdown
  - **Live play-by-play feed**
  - **Cumulative team scores** and **individual player scores** (sorted high → low)
  - **Scoring rules:**  
    - +10 for tagging opponent  
    - −10 for tagging same team (both tagger & tagged)  
    - Base codes:  
      - `53`: Red base scored → Green team +100 points, base icon added  
      - `43`: Green base scored → Red team +100 points, base icon added
  - High team score flashes during play
  - Random MP3 track plays during the game, synced to countdown
- End of game:
  - Broadcast code **221** three times
  - Remain on game screen with scores; operator can return to player entry

---

## 📂 Assets

This project includes only the assets needed from the instructor’s [photon-main](https://github.com/jstrother123/photon-main) repository.  

---

## 🖥️ System Requirements

- **Debian 12+ VM** (provided by instructor)
- **PostgreSQL** with database `photon` and table `players` already installed
- Internet access (for package installs)

---

## 📦 Installation

Clone the repo into your Debian VM:

```bash
git clone [https://github.com/huntrhill/Photon.git](https://github.com/huntrhill/Photon.git)
cd Photon
chmod +x install.sh
./install.sh
```
---

## 👥 Team

| GitHub | Real Name | Role |
|---|---|---|
| @huntrhill | Hunter Hill       | Lead / UI - Entry            |
| @member2   | Chance Pickett    | UI – Splash/Scoring          |
| @member3   | Michael Purtle    | Networking/Audio / UI – Game |
| @coaluh    | Cody Uhl           | QA / Docs / Architecture      |

> All team members used real names on GitHub or are cross-referenced above.

---

## 🔌 Quick Test (after install)

Open **Terminal A** (listener for 7500):
```bash
python3 - <<'PY'
import socket
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.bind(("0.0.0.0",7500))
print("Listening on 0.0.0.0:7500…")
while True: print(s.recvfrom(4096)[0].decode().strip())
PY

