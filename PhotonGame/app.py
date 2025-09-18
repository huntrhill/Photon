import asyncio, sys, time
from PyQt5 import QtWidgets, QtCore
from .net import udp_sender, udp_receiver
from .scoring import State, handle_rx
from .audio import init_tracks, play_random
from . import ui

class Controller(QtCore.QObject):
    # Signals to decouple UI from logic if you want later
    updated = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.tx_queue = asyncio.Queue()
        self.state = State()
        self.tracks = []
        self.game_running = False
        self.seconds_left = 0

    def send_int(self, val:int):
        self.tx_queue.put_nowait(int(val))

    # === Game lifecycle ===
    def start_pre_game(self):
        """Start 30s warning, play music, then start game."""
        if self.game_running: return
        self.seconds_left = 30 + 6*60  # 30s warn + 6 min
        # kick off music exactly when pre-game starts
        play_random(self.tracks)
        self.game_running = True

    def tick(self):
        """Called every 1s by a QTimer; handles countdown + broadcasts."""
        if not self.game_running: return
        if self.seconds_left == 0:
            return
        self.seconds_left -= 1

        # T= pre-game boundary: when we cross from 30->29, nothing special
        # At exactly the start of gameplay: when remaining == 6*60 (after 30s elapsed)
        if self.seconds_left == 6*60:
            # Game start code 202
            self.send_int(202)

        # Game end
        if self.seconds_left == 0:
            for _ in range(3):
                self.send_int(221)
                QtCore.QThread.msleep(200)  # slight spacing
            self.game_running = False

        self.updated.emit()

async def run_app():
    app = QtWidgets.QApplication(sys.argv)

    ctrl = Controller()

    # Load audio tracks (assets/tracks)
    # If your assets are at PhotonGame/assets, adjust this path in ui.build_main_window
    # We pass tracks into controller after UI picks a root path to keep it simple.
    win, splash, entry, game, assets_path = ui.build_main_window(ctrl)

    # init audio after we know assets_path
    ctrl.tracks = init_tracks(assets_path)

    # Wire simple UI actions
    entry.addPlayerRequested.connect(lambda pid, codename, eqid, team: on_add_player(ctrl, entry, pid, codename, eqid, team))
    entry.startRequested.connect(lambda: on_start(ctrl, win, game))
    entry.clearRequested.connect(lambda: on_clear(ctrl, entry))

    game.backRequested.connect(lambda: win.setCurrentIndex(1))  # back to entry
    ctrl.updated.connect(lambda: game.refresh(ctrl.state, ctrl.seconds_left))

    # Timers:
    tick_timer = QtCore.QTimer()
    tick_timer.timeout.connect(ctrl.tick)
    tick_timer.start(1000)

    # UDP plumbing
    async def on_rx(line: str):
        handle_rx(ctrl.state, line, ctrl.send_int)
        game.refresh(ctrl.state, ctrl.seconds_left)

    asyncio.create_task(udp_sender(ctrl.tx_queue))
    asyncio.create_task(udp_receiver(on_rx))

    win.setCurrentIndex(0)  # splash
    splash.start()

    sys.exit(app.exec_())

def on_add_player(ctrl: Controller, entry, pid: int, codename: str|None, eqid: int, team: str):
    """
    - Lookup/add player in DB via entry helper; entry handles prompting codename if missing.
    - Assign team in state
    - Broadcast equipment id immediately
    """
    row = entry.get_or_create_player(pid, codename)
    ctrl.state.codename[pid] = row["codename"]
    ctrl.state.team[pid] = team
    ctrl.send_int(eqid)  # immediate broadcast per spec
    entry.add_to_roster(pid, row["codename"], team)

def on_start(ctrl: Controller, win, game):
    if not ctrl.game_running:
        ctrl.start_pre_game()
        win.setCurrentIndex(2)  # show game screen
        game.refresh(ctrl.state, ctrl.seconds_left)

def on_clear(ctrl: Controller, entry):
    ctrl.state = State()
    entry.clear_rosters()
