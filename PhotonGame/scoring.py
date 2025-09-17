from collections import defaultdict

class GameState:
    def __init__(self):
        self.team = {}           # player_id -> 'red'|'green'
        self.codename = {}       # player_id -> string
        self.base_rewarded = set()  # player_ids who've received base icon reward
        self.score = defaultdict(int)
        self.play_by_play = []

    def add_event(self, text): self.play_by_play.append(text)

def handle_rx_line(state: GameState, line: str, send):
    # send(...) should queue a broadcast integer on 7500
    # Formats:
    #   "tx:hit" -> broadcast hit; if friendly fire also broadcast tx
    #   "53" -> red base scored: all GREEN get +100 & icon
    #   "43" -> green base scored: all RED get +100 & icon
    try:
        if ":" in line:
            tx, hit = map(int, line.split(":", 1))
            team_tx  = state.team.get(tx)
            team_hit = state.team.get(hit)
            # announce hit (required)
            send(hit)
            # scoring
            if team_tx and team_hit:
                if team_tx == team_hit:      # friendly fire
                    state.score[tx]  -= 10
                    state.score[hit] -= 10
                    state.add_event(f"Friendly fire! {tx} ↔ {hit} (-10 each)")
                    # and broadcast tx as well (two transmissions)
                    send(tx)
                else:                         # normal hit
                    state.score[tx] += 10
                    state.add_event(f"{tx} tagged {hit} (+10)")
        else:
            code = int(line)
            if code == 53:    # red base scored → GREEN players +100
                for pid, t in state.team.items():
                    if t == "green":
                        state.score[pid] += 100
                        state.base_rewarded.add(pid)
                state.add_event("Red base scored! Green team +100.")
            elif code == 43:  # green base scored → RED players +100
                for pid, t in state.team.items():
                    if t == "red":
                        state.score[pid] += 100
                        state.base_rewarded.add(pid)
                state.add_event("Green base scored! Red team +100.")
    except Exception as e:
        state.add_event(f"RX parse error: {line} ({e})")
