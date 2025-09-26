import os, random, pygame
from pathlib import Path
def init_tracks(path):
	pygame.mixer.init()
	assests = Path(path)
	
	tracks_dir = assests if assests.name == "tracks" else (assests / "tracks")
	mp3s = sorted(p for p in tracks_dir.iterdir() if p.is_file() and p.suffix.lower() == ".mp3")
	return mp3s

def play_random(tracks):
	if not tracks: return
	pygame.mixer.music.load(random.choice(tracks))
	pygame.mixer.music.play()

