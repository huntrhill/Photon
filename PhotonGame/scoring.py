from collections import defaultdict
from typing import Optional

class State:
    def __init__(self):
       self.team = {}         # eqid -> 'red'|'green'
       self.codename = {}     # eqid -> string
       self.score = defaultdict(int)
       self.base_icon = set() # eqid that earned base icon
       self.feed = []
       self.eq_to_pid = {}    # eqid -> player-id (DB id, the one you want to display)


    def add(self, s): self.feed.append(s)
    
    def register_players(self, players):
        """
        players: iterable of (pid, team, codename)
        pid should match exactly what comes over the wire in handle_rx.
        """
        self.team.clear()
        self.codename.clear()
        self.score.clear()
        self.base_icon.clear()

        for pid, team, name in players:
            pid = int(pid)              # normalize to int
            team = team.lower().strip() # 'red' or 'green'
            self.team[pid] = team
            self.codename[pid] = name
            self.score[pid] = 0

        self.add(f"Registered {len(players)} players.")

def _award_base(state: "State", code: int, scorer_pid: Optional[int] = None):
    if code == 53:
        scoring_team = "green"
    elif code == 43:
        scoring_team = "red"
    else:
        return

    if scorer_pid is not None:
        if state.team.get(scorer_pid) == scoring_team:
            state.score[scorer_pid] += 100

            # *** make base_icon point ONLY at the latest scorer ***
            state.base_icon.clear()
            state.base_icon.add(scorer_pid)

            state.add(f"{scoring_team.capitalize()} base scored by {scorer_pid} (+100).")
        else:
            state.add(f"Inconsistent base event {code} from {scorer_pid} (team mismatch).")
    else:
        state.add(f"{scoring_team.capitalize()} base scored (+100), scorer unknown.")

def _get_team(state, pid):
    return state.team.get(pid) or state.team.get(str(pid))

def _is_base_code(rhs_int: int) -> bool:
    # Base units are 43 and 53, period.
    return rhs_int in (43, 53)
    
def _ensure_team(state: State, pid: int) -> str:
    """
    Return the team for this pid, auto-registering if needed.
    """
    # Already known?
    team = _get_team(state, pid)
    if team:
        return team

    # Auto-assign: keep team sizes roughly balanced
    red_count   = sum(1 for t in state.team.values() if t == "red")
    green_count = sum(1 for t in state.team.values() if t == "green")

    if red_count <= green_count:
        team = "red"
    else:
        team = "green"

    state.team[pid] = team
    state.add(f"Auto-registered pid={pid} as team {team}")
    return team

def handle_rx(state: State, line: str, send_int):
    try:
        line = line.strip()
        if ":" in line:
            tx_str, rhs_str = line.split(":", 1)
            tx = int(tx_str)
            rhs = int(rhs_str.strip())

            # 1) Base events: 43/53 on RHS
            if _is_base_code(rhs):
                _award_base(state, rhs, scorer_pid=tx)
                send_int(tx)
                #send_int(rhs)
                return

            # 2) Normal player hit
            hit = rhs
            send_int(hit)  # if this loops back, it will be a no-op on your side
            t_tx  = _get_team(state, tx)
            t_hit = _get_team(state, hit)
            if not (t_tx and t_hit):
                state.add(
                    f"IGNORED hit {tx}->{hit}: unknown team(s) "
                    f"(tx={t_tx}, hit={t_hit}). Register players first."
                )
                return

            if t_tx == t_hit:
                state.score[int(tx)]  -= 10
                state.score[int(hit)] -= 10
                send_int(tx)
                state.add(f"FF: {tx} ↔ {hit} (-10 each)")
            else:
                state.score[int(tx)] += 10
                state.add(f"{tx} tagged {hit} (+10)")

        else:
            # Bare codes (e.g., 43/53). Treat as base with unknown scorer.
            code = int(line)
            if _is_base_code(code):
                _award_base(state, code, scorer_pid=None)
            else:
                state.add(f"Ignored bare code {code}")
    except Exception as e:
        state.add(f"Bad packet: {line} ({e})")
