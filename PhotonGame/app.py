import asyncio, sys
from PyQt5 import QtWidgets, QtCore
from qasync import QEventLoop, asyncSlot

from .net import udp_sender, udp_receiver
from .scoring import State, handle_rx
from .audio import init_tracks, play_random
from . import build_main_window  # from package-local __init__.py

class Controller(QtCore.QObject):
    updated = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.tx_queue = asyncio.Queue()
        self.state = State()
        self.tracks = []
        self.game_running = False
        self.seconds_left = 0

    def send_int(self, val: int):
        self.tx_queue.put_nowait(int(val))

    def start_pre_game(self):
        if self.game_running:
            return
        self.seconds_left = 30 + 6 * 60  # 30s warn + 6min game
        play_random(self.tracks)
        self.game_running = True

    def tick(self):
        if not self.game_running:
            return
        if self.seconds_left == 0:
            return
        self.seconds_left -= 1

        if self.seconds_left == 6 * 60:
            self.send_int(202)  # game start

        if self.seconds_left == 0:
            for _ in range(3):
                self.send_int(221)  # game end x3
                QtCore.QThread.msleep(200)
            self.game_running = False

        self.updated.emit()

def run_app():
    # Create Qt app and bind asyncio to Qt's loop via qasync
    app = QtWidgets.QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    ctrl = Controller()
    win, splash, entry, game, assets_path = build_main_window(ctrl)

    # init audio after assets path is known
    ctrl.tracks = init_tracks(assets_path)

    # wire UI
    entry.addPlayerRequested.connect(lambda pid, codename, eqid, team:
                                     on_add_player(ctrl, entry, pid, codename, eqid, team))
    entry.startRequested.connect(lambda: on_start(ctrl, win, game))
    entry.clearRequested.connect(lambda: on_clear(ctrl, entry))

    game.backRequested.connect(lambda: win.setCurrentIndex(1))
    ctrl.updated.connect(lambda: game.refresh(ctrl.state, ctrl.seconds_left))

    # 1s game tick
    tick_timer = QtCore.QTimer()
    tick_timer.timeout.connect(ctrl.tick)
    tick_timer.start(1000)

    # UDP coroutines run on the same loop as Qt now
    async def on_rx(line: str):
        handle_rx(ctrl.state, line, ctrl.send_int)
        game.refresh(ctrl.state, ctrl.seconds_left)

    asyncio.create_task(udp_sender(ctrl.tx_queue))
    asyncio.create_task(udp_receiver(on_rx))

    win.setCurrentIndex(0)
    splash.start()

    # Run the unified Qt+asyncio loop
    with loop:
        sys.exit(loop.run_forever())

def on_add_player(ctrl: Controller, entry, pid: int, codename: str | None, eqid: int, team: str):
    row = entry.get_or_create_player(pid, codename)
    # normalize row shape (dict or tuple)
    if isinstance(row, dict):
        pid2, codename2 = row.get("id"), row.get("codename")
    else:
        pid2, codename2 = row  # (id, codename)
    ctrl.state.codename[pid2] = codename2
    ctrl.state.team[pid2] = team
    ctrl.send_int(eqid)  # broadcast equipment id immediately
    entry.add_to_roster(pid2, codename2, team)

def on_start(ctrl: Controller, win, game):
    if not ctrl.game_running:
        ctrl.start_pre_game()
        win.setCurrentIndex(2)
        game.refresh(ctrl.state, ctrl.seconds_left)

def on_clear(ctrl: Controller, entry):
    ctrl.state = State()
    entry.clear_rosters()
