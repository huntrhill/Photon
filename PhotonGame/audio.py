import os, random, pygame
from pathlib import Path

# folders we will search *under the assets root*
DEFAULT_TRACK_DIRS = ("audio/tracks", "tracks", "GameSounds", "audio/sfx", "sfx")
AUDIO_EXTS = (".mp3", ".wav")

def init_tracks(assets_root: str, subdirs=DEFAULT_TRACK_DIRS):
    """
    assets_root: path to PhotonGame/assets (we'll scan common subdirs)
    Returns a list of absolute file paths to audio tracks.
    """
    pygame.mixer.init()
    root = Path(assets_root)
    found = []
    for rel in subdirs:
        p = (root / rel)
        if p.is_dir():
            for f in sorted(p.iterdir()):
                if f.is_file() and f.suffix.lower() in AUDIO_EXTS:
                    found.append(str(f))
    # also allow a flat drop-in directly at assets_root (rare, but harmless)
    for f in root.iterdir():
        if f.is_file() and f.suffix.lower() in AUDIO_EXTS:
            found.append(str(f))
    return found

def play_random(tracks):
    if not tracks: 
        return
    pygame.mixer.music.load(random.choice(tracks))
    pygame.mixer.music.play()
