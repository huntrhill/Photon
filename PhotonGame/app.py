# PhotonGame/app.py
import asyncio, sys, os
from PyQt5 import QtWidgets, QtCore
from qasync import QEventLoop

from .net import udp_sender, udp_receiver, Endpoints, endpoints_from_env
from .scoring import State, handle_rx
from .audio import init_audio, play_random_music, stop_music, play_sfx
from . import build_main_window  # from package-local __init__.py


class Controller(QtCore.QObject):
    updated = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.tx_queue = asyncio.Queue()
        self.state = State()
        self.tracks = []
        self.sfx = {}
        self.game_running = False
        self.seconds_left = 0

        # Network endpoints + task handles
        self.endpoints: Endpoints = endpoints_from_env()
        self._stop_event: asyncio.Event | None = None
        self._tasks: tuple[asyncio.Task, asyncio.Task] | tuple = ()

    def send_int(self, val: int):
        self.tx_queue.put_nowait(int(val))

    # ---------- Game lifecycle ----------
    def start_pre_game(self):
        if self.game_running:
            return
        self.seconds_left = 30 + 6 * 60  # 30s warning + 6min game
        play_sfx(self.sfx, "start")
        play_random_music(self.tracks)
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
            # finish SFX + stop music
            play_sfx(self.sfx, "end")
            stop_music()
            self.game_running = False

        self.updated.emit()

    # ---------- Networking (qasync-friendly) ----------
    def start_network(self, on_rx_coro):
        """Start UDP sender/receiver tasks for current endpoints."""
        if self._stop_event is not None:
            return
        self._stop_event = asyncio.Event()
        sender_task = asyncio.create_task(udp_sender(self.tx_queue, self.endpoints, self._stop_event))
        receiver_task = asyncio.create_task(udp_receiver(on_rx_coro, self.endpoints, self._stop_event))
        self._tasks = (sender_task, receiver_task)

    async def stop_network(self):
        if self._stop_event is None:
            return
        self._stop_event.set()
        for t in self._tasks:
            t.cancel()
        await asyncio.sleep(0.05)  # give sockets a moment to close
        self._stop_event = None
        self._tasks = ()

    async def rebind_network(self, new_ep: Endpoints, on_rx_coro):
        await self.stop_network()
        self.endpoints = new_ep
        self.start_network(on_rx_coro)


def run_app():
    # Qt app + unified asyncio loop (qasync)
    app = QtWidgets.QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    ctrl = Controller()
    win, splash, entry, game, assets_path = build_main_window(ctrl)

    # audio after assets path known
    audio = init_audio(assets_path)
    ctrl.tracks = audio["tracks"]
    ctrl.sfx    = audio["sfx"]

    # wire UI
    entry.addPlayerRequested.connect(
        lambda pid, codename, eqid, team: on_add_player(ctrl, entry, pid, codename, eqid, team)
    )
    entry.startRequested.connect(lambda: on_start(ctrl, win, game))
    entry.clearRequested.connect(lambda: on_clear(ctrl, entry))
    add_settings_button(entry, ctrl, win, game)  # Settings button

    game.backRequested.connect(lambda: win.setCurrentIndex(1))
    ctrl.updated.connect(lambda: game.refresh(ctrl.state, ctrl.seconds_left))

    # timer tick
    tick_timer = QtCore.QTimer()
    tick_timer.timeout.connect(ctrl.tick)
    tick_timer.start(1000)

    # UDP coroutines share this loop
    async def on_rx(line: str):
        # Update scoring first
        handle_rx(ctrl.state, line, ctrl.send_int)

        # SFX selection
        parts = line.split(":", 1)
        if len(parts) == 2:
            tx, rhs = parts[0].strip(), parts[1].strip()
            if rhs in ("43", "53"):
                # base scored
                play_sfx(ctrl.sfx, "intruder")
            else:
                # player tag: decide friendly vs normal
                try:
                    tx_i, hit_i = int(tx), int(rhs)
                    t_tx  = ctrl.state.team.get(tx_i)
                    t_hit = ctrl.state.team.get(hit_i)
                    if t_tx and t_hit and t_tx == t_hit:
                        play_sfx(ctrl.sfx, "hitown")   # friendly fire
                    else:
                        play_sfx(ctrl.sfx, "hit")      # normal hit
                except ValueError:
                    pass

        game.refresh(ctrl.state, ctrl.secon
