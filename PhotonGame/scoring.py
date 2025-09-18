from collections import defaultdict

class State:
    def __init__(self):
        self.team = {}         # pid -> 'red'|'green'
        self.codename = {}     # pid -> string
        self.score = defaultdict(int)
        self.base_icon = set() # players that earned base icon
        self.feed = []

    def add(self, s): self.feed.append(s)

def handle_rx(state: State, line: str, send_int):
    try:
        if ":" in line:
            tx, hit = map(int, line.split(":", 1))
            send_int(hit)  # always broadcast who was hit
            t_tx, t_hit = state.team.get(tx), state.team.get(hit)
            if t_tx and t_hit:
                if t_tx == t_hit:
                    state.score[tx]  -= 10
                    state.score[hit] -= 10
                    send_int(tx)  # second transmission
                    state.add(f"FF: {tx} ↔ {hit} (-10 each)")
                else:
                    state.score[tx] += 10
                    state.add(f"{tx} tagged {hit} (+10)")
        else:
            code = int(line)
            if code == 53: # red base scored -> green +100
                for pid, team in state.team.items():
                    if team == "green":
                        state.score[pid] += 100
                        state.base_icon.add(pid)
                state.add("Red base scored → Green +100.")
            elif code == 43: # green base scored -> red +100
                for pid, team in state.team.items():
                    if team == "red":
                        state.score[pid] += 100
                        state.base_icon.add(pid)
                state.add("Green base scored → Red +100.")
    except Exception as e:
        state.add(f"Bad packet: {line} ({e})")
