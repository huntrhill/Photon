import os, random, pygame
def init_tracks(path):
    pygame.mixer.init()
    p = os.path.join(path, "tracks")
    return [os.path.join(p,f) for f in os.listdir(p) if f.lower().endswith(".mp3")]

def play_random(tracks):
    if not tracks: return
    pygame.mixer.music.load(random.choice(tracks))
    pygame.mixer.music.play()
