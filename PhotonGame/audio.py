# PhotonGame/audio.py
from pathlib import Path
import random
import pygame

AUDIO_EXTS_MUSIC = {".mp3"}
AUDIO_EXTS_SFX   = {".wav", ".ogg"}

def _safe_init():
    if not pygame.mixer.get_init():
        pygame.mixer.init()

def _load_sound(p: Path):
    try:
        return pygame.mixer.Sound(str(p))
    except Exception:
        return None

def init_audio(assets_root: str):
    """
    Loads background tracks (MP3) and common SFX.
    Returns:
      {"tracks": [str mp3 paths...], "sfx": {name: pygame.Sound|None}}
    """
    _safe_init()
    root = Path(assets_root)

    # --- music ---
    tracks = []
    tdir = root / "tracks"
    if tdir.is_dir():
        for f in sorted(tdir.iterdir()):
            if f.is_file() and f.suffix.lower() in AUDIO_EXTS_MUSIC:
                tracks.append(str(f))

    # --- GameSounds ---
    gs = {}
    gdir = root / "GameSounds"
    if gdir.is_dir():
        for f in gdir.iterdir():
            if f.is_file() and f.suffix.lower() in AUDIO_EXTS_SFX:
                gs[f.name.lower()] = _load_sound(f)

    # expected names (case-insensitive)
    # map multiple options to canonical keys
    sfx = {
        "start": gs.get("photon-start.wav"),
        "end":   gs.get("photon-close-program.wav") or gs.get("photon-exit.wav"),
        "intruder": gs.get("photon-intruder.wav"),
        "emptybin": gs.get("photon-empty-bin.wav"),
    }

    # --- sfx (gameplay) ---
    sfxdir = root / "sfx"
    if sfxdir.is_dir():
        names = {f.name.lower(): f for f in sfxdir.iterdir()
                 if f.is_file() and f.suffix.lower() in AUDIO_EXTS_SFX}
        sfx["hit"]    = _load_sound(names.get("hit.wav")) or _load_sound(names.get("gethit.wav"))
        sfx["hitown"] = _load_sound(names.get("hitown.wav"))  # friendly fire
        sfx["miss"]   = _load_sound(names.get("miss.wav"))
        sfx["reset"]  = _load_sound(names.get("reset.wav"))

    return {"tracks": tracks, "sfx": sfx}

def play_random_music(tracks):
    _safe_init()
    if not tracks:
        return
    pygame.mixer.music.load(random.choice(tracks))
    pygame.mixer.music.play()

def stop_music():
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()

def play_sfx(sfx_map: dict, key: str):
    snd = sfx_map.get(key)
    if snd is not None:
        try:
            snd.play()
        except Exception:
            pass
