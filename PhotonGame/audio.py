import os, random, pygame
from pathlib import Path

def init_tracks(tracks_path):
    pygame.mixer.init()
    p = Path(tracks_path)  # this should already be assets/audio/tracks
    return sorted([str(f) for f in p.iterdir() if f.is_file() and f.suffix.lower() in (".mp3", ".wav")])

def play_random(tracks):
    if not tracks: return
    pygame.mixer.music.load(random.choice(tracks))
    pygame.mixer.music.play()
