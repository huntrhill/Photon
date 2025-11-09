import os, random, pygame, sys, io

# ---------- robust mixer init ----------
def _init_mixer():
    # Try to initialize; if it fails, try a couple of common drivers and a 'dummy' fallback
    tried = []
    for driver in (os.getenv("SDL_AUDIODRIVER"), "pulseaudio", "alsa", "dsp", "dummy"):
        if not driver:
            continue
        try:
            os.environ["SDL_AUDIODRIVER"] = driver
            pygame.mixer.quit()
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            # quick sanity: get_init returns (freq, format, channels) or None
            if pygame.mixer.get_init():
                return True
        except Exception as e:
            tried.append((driver, str(e)))
    # last attempt with defaults
    try:
        pygame.mixer.quit()
        pygame.mixer.init()
        return pygame.mixer.get_init() is not None
    except Exception as e:
        tried.append(("default", str(e)))
        print("[audio] Mixer init failed:", tried, file=sys.stderr)
        return False

def _is_probably_mp3(path: str) -> bool:
    # quick sniff: start with 'ID3' or an MPEG frame sync 0xFFEx
    try:
        with open(path, "rb") as f:
            head = f.read(4)
        if head.startswith(b"ID3"):
            return True
        if len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0:
            return True
    except Exception:
        pass
    return False

def _find_files(root: str, sub: str, exts: tuple[str, ...]):
    base = os.path.join(root, sub)
    if not os.path.isdir(base):
        return []
    return [
        os.path.join(base, f)
        for f in os.listdir(base)
        if os.path.isfile(os.path.join(base, f)) and f.lower().endswith(exts)
    ]

def init_audio(assets_dir: str):
    """
    Initialize pygame mixer and load:
      - tracks: MP3 files under assets/tracks/
      - sfx: WAV files under assets/sfx/ and assets/GameSounds/
    Returns dict: {"tracks": [paths], "sfx": {"start": Sound, "end": Sound, "hit": Sound, ...}}
    """
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.init()

    if not _init_mixer():
        print("[audio] WARNING: Mixer not initialized; audio will be disabled.", file=sys.stderr)
        return {"tracks": [], "sfx": {}}

    # ---- tracks (MP3) ----
    track_paths = _find_files(assets_dir, "tracks", (".mp3",))
    # filter out likely-non-mp3 files (e.g., LFS pointers)
    track_paths = [p for p in track_paths if _is_probably_mp3(p)]

    # ---- SFX (WAV) ----
    sfx = {}
    def load_wav_safe(path):
        try:
            return pygame.mixer.Sound(path)
        except Exception as e:
            print(f"[audio] Failed to load sfx {path}: {e}", file=sys.stderr)
            return None

    # Preferred names based on your layout
    # GameSounds: Photon-Start.wav, Photon-Exit.wav, Photon-Intruder.wav, Photon-Close-Program.wav
    # sfx: hit.wav, hitown.wav, gethit.wav, miss.wav, reset.wav
    gs = os.path.join(assets_dir, "GameSounds")
    sfx_dir = os.path.join(assets_dir, "sfx")

    mapping = {
        "start": os.path.join(gs, "Photon-Start.wav"),
        "end":   os.path.join(gs, "Photon-Exit.wav"),
        "intruder": os.path.join(gs, "Photon-Intruder.wav"),
        "close": os.path.join(gs, "Photon-Close-Program.wav"),
        "hit":   os.path.join(sfx_dir, "hit.wav"),
        "hitown":os.path.join(sfx_dir, "hitown.wav"),
        "gethit":os.path.join(sfx_dir, "gethit.wav"),
        "miss":  os.path.join(sfx_dir, "miss.wav"),
        "reset": os.path.join(sfx_dir, "reset.wav"),
    }

    for key, path in mapping.items():
        if os.path.isfile(path):
            snd = load_wav_safe(path)
            if snd:
                sfx[key] = snd

    return {"tracks": track_paths, "sfx": sfx}

# ---------- playback helpers ----------
def is_music_playing() -> bool:
    try:
        return pygame.mixer.music.get_busy()
    except Exception:
        return False
        
def stop_music():
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass

def play_random_music(tracks: list[str]):
    if not tracks:
        return
    # Stop any existing stream before (re)loading
    stop_music()

    # Shuffle through candidates until one loads/plays or we run out
    shuffled = tracks[:]
    random.shuffle(shuffled)
    for p in shuffled:
        try:
            pygame.mixer.music.load(p)
            pygame.mixer.music.play()
            return
        except Exception as e:
            # Bad file? Log and try the next one
            print(f"[audio] Skipping track {p}: {e}", file=sys.stderr)
            continue
    print("[audio] No playable MP3 tracks found.", file=sys.stderr)

def play_sfx(sfx: dict, name: str):
    snd = sfx.get(name)
    if not snd:
        return
    try:
        snd.play()
    except Exception as e:
        print(f"[audio] SFX '{name}' failed: {e}", file=sys.stderr)

def play_random_music_for_seconds(tracks: list[str], seconds: int = 30):
    """
    Pick a random MP3 from `tracks`, play it immediately,
    and fade to silence exactly when `seconds` elapse.
    Used for syncing pre-game countdown music.
    """
    if seconds <= 0:
        print("[audio] Invalid countdown duration; skipping music.")
        return

    # don't double-start if something is already playing
    if is_music_playing():
        return
    stop_music()  # ensure a clean start
    if not tracks:
        print("[audio] No tracks to play.")
        return

    shuffled = tracks[:]
    random.shuffle(shuffled)

    for p in shuffled:
        try:
            pygame.mixer.music.load(p)
            pygame.mixer.music.set_volume(1.0)  # full volume (adjust if needed)
            pygame.mixer.music.play()
            # Sync fadeout with requested total duration
            pygame.mixer.music.fadeout(int(seconds * 1000))
            # print(f"[audio] Now playing: {os.path.basename(p)} ({seconds}s)")
            return
        except Exception as e:
            print(f"[audio] Skipping track {p}: {e}", file=sys.stderr)
            continue

    print("[audio] No playable MP3 tracks found.", file=sys.stderr)
