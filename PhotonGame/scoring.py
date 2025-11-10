from collections import defaultdict

class State:
    def __init__(self):
        self.team = {}         # pid -> 'red'|'green'
        self.codename = {}     # pid -> string
        self.score = defaultdict(int)
        self.base_icon = set() # players that earned base icon
        self.feed = []

    def add(self, s): self.feed.append(s)

def _award_base(state: "State", code: int):
    # 53 => Red base scored -> Green +100
    # 43 => Green base scored -> Red +100
    if code == 53:
        for pid, team in state.team.items():
            if team == "green":
                state.score[pid] += 100
                state.base_icon.add(pid)
        state.add("Red base scored → Green +100.")
    elif code == 43:
        for pid, team in state.team.items():
            if team == "red":
                state.score[pid] += 100
                state.base_icon.add(pid)
        state.add("Green base scored → Red +100.")

def handle_rx(state: State, line: str, send_int):
    try:
        line = line.strip()
        if ":" in line:
            tx_str, rhs = line.split(":", 1)
            tx = int(tx_str)
            # Base codes can appear on RHS (pid:43 / pid:53)
            if rhs in ("43", "53"):
                _award_base(state, int(rhs))
                return
            # Normal tag: tx:hit
            hit = int(rhs)
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
            # Bare codes (e.g., 43 or 53 sent alone)
            code = int(line)
            if code in (43, 53):
                _award_base(state, code)
    except Exception as e:
        state.add(f"Bad packet: {line} ({e})")
