from PyQt5 import QtWidgets, QtCore, QtGui
import os
from enum import Enum
import time
import math
from typing import Optional

class Phase(Enum):
	COUNTDOWN = 1
	RUNNING = 2
	ENDED = 3

class GameScreen(QtWidgets.QWidget):
	backRequested = QtCore.pyqtSignal()
	gameStarted   = QtCore.pyqtSignal()
	gameEnded     = QtCore.pyqtSignal()
	
	def __init__(self, parent=None, assets_dir=""):
		super().__init__(parent)
		self.assets_dir = assets_dir
		self._base_icon = None
		p = os.path.join(self.assets_dir, "images", "baseicon.jpg")
		if os.path.exists(p):
			self._base_icon = QtGui.QIcon(p)
	
		self._build_ui()
		self._install_timers()
		self._countdown_deadline = None
		self._game_deadline = None

	def _install_timers(self):
		self._flash_timer = QtCore.QTimer(self)
		self._flash_timer.setTimerType(QtCore.Qt.PreciseTimer)
		self._flash_timer.timeout.connect(self._pulse)
		self._flash_timer.start(500)
	
		self._countdown_timer = QtCore.QTimer(self)
		self._countdown_timer.setTimerType(QtCore.Qt.PreciseTimer)
		self._countdown_timer.setInterval(200)
		self._countdown_timer.timeout.connect(self._tick_countdown)
	
		self._game_timer = QtCore.QTimer(self)
		self._game_timer.setTimerType(QtCore.Qt.PreciseTimer)
		self._game_timer.setInterval(250)
		self._game_timer.timeout.connect(self._tick_game)

	def _build_ui(self):
		v = QtWidgets.QVBoxLayout(self)
		v.setContentsMargins(12,12,12,12)
		v.setSpacing(8)
	
		# Top: timer + team totals
		top = QtWidgets.QHBoxLayout()
		self.timer_lbl = QtWidgets.QLabel('6:30', alignment=QtCore.Qt.AlignCenter)
		self.timer_lbl.setStyleSheet("font-size:28px; font-weight:600;")
		self.red_total = QtWidgets.QLabel("Red: 0", alignment=QtCore.Qt.AlignCenter)
		self.green_total = QtWidgets.QLabel("Green: 0", alignment=QtCore.Qt.AlignCenter)
		top.addWidget(self.timer_lbl,1); top.addWidget(self.red_total,1); top.addWidget(self.green_total,1)
		v.addLayout(top)
	
		# Middle: play-by-play
		self.feed = QtWidgets.QListWidget()
		v.addWidget(self.feed, 2)
	
		# Bottom: per-team tables
		bottom = QtWidgets.QHBoxLayout()
		self.red_table = self._make_table()
		self.green_table = self._make_table()
		bottom.addWidget(self._wrap_group("Red", self.red_table))
		bottom.addWidget(self._wrap_group("Green", self.green_table))
		v.addLayout(bottom, 2)
	
		# Back button
		back_btn = QtWidgets.QPushButton("Back to Entry")
		back_btn.clicked.connect(self.backRequested.emit)
		v.addWidget(back_btn, 0, alignment=QtCore.Qt.AlignRight)
	
		# Big overlay label for pre-game countdown
		self.countdownLabel = QtWidgets.QLabel("", self)
		self.countdownLabel.setAlignment(QtCore.Qt.AlignCenter)
		self.countdownLabel.setStyleSheet(
			"font-size:96px; font-weight:800; color:#fff; background:rgba(0,0,0,0.35);"
		)
		self.countdownLabel.hide()
		self.countdownLabel.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)

	def resizeEvent(self, e):
		super().resizeEvent(e)
		if self.countdownLabel:
			self.countdownLabel.setGeometry(self.rect())

	def _make_table(self):
		t = QtWidgets.QTableWidget(0, 3)
		t.setHorizontalHeaderLabels(["ID", "Codename", "Score"])
		t.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		t.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		t.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		t.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		t.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
		t.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
		return t

	def _wrap_group(self, title, widget):
		box = QtWidgets.QGroupBox(title)
		lay = QtWidgets.QVBoxLayout(box); lay.addWidget(widget)
		return box

    # ---- API used by app.py ----
	def refresh(self, state, seconds_left: Optional[int] = int):
		# (Do NOT update the timer label here; the timer handlers own it)
		# Totals
		red_total = sum(s for pid, s in state.score.items() if state.team.get(pid) == "red")
		green_total = sum(s for pid, s in state.score.items() if state.team.get(pid) == "green")
		self.red_total.setText(f"Red: {red_total}")
		self.green_total.setText(f"Green: {green_total}")
	
		# Feed (show last 200)
		self.feed.clear()
		for line in state.feed[-200:]:
			self.feed.addItem(line)
	
		# Tables
		self._fill_team_table(self.red_table, state, "red")
		self._fill_team_table(self.green_table, state, "green")
	
		# Leader for flashing
		self._leader = "red" if red_total > green_total else ("green" if green_total > red_total else None)
	
		# Optional one-time resync if you reconnect mid-match and the backend has the truth:
		# if self.phase == Phase.RUNNING and seconds_left is not None and self._game_deadline is None:
		#     self._game_deadline = time.monotonic() + int(seconds_left)

	def _fill_team_table(self, table, state, team):
		rows = [(pid, state.codename.get(pid, ""), state.score.get(pid, 0))
				for pid,t in state.team.items() if t == team]
		rows.sort(key=lambda x: x[2], reverse=True)  # by score desc
		table.setRowCount(len(rows))
		for r,(pid,name,score) in enumerate(rows):
			table.setItem(r, 0, QtWidgets.QTableWidgetItem(str(pid)))
			name_item = QtWidgets.QTableWidgetItem(name)
			# safer: only use base_icon if present on state
			try:
				has_icon = (pid in state.base_icon)
			except AttributeError:
				has_icon = False
			if has_icon and self._base_icon is not None:
				name_item.setIcon(self._base_icon)
			table.setItem(r, 1, name_item)
			table.setItem(r, 2, QtWidgets.QTableWidgetItem(str(score)))

	def _pulse(self):
		# Flash the label of the leader
		leader = getattr(self, "_leader", None)
		if leader == "red":
			lab = self.red_total
		elif leader == "green":
			lab = self.green_total
		else:	
			return  # nobody is leading yet, nothing to flash
	
		self._flash_on = not self._flash_on
		if lab is self.red_total:
			lab.setStyleSheet("font-weight:bold; color: red;" if self._flash_on else "font-weight:bold; color: darkred;")
		else:
			lab.setStyleSheet("font-weight:bold; color: green;" if self._flash_on else "font-weight:bold; color: darkgreen;")

    # ---------------- Countdown + Game control ----------------
	def reset_to_idle(self, default_secs: int = 6*60 + 30):
		"""Fully stop timers and reset labels so a new start always works."""
		self._countdown_timer.stop()
		self._game_timer.stop()
		self.countdownLabel.hide()
		self.phase = Phase.ENDED
		self._leader = None
		self._countdown_deadline = None
		self._game_deadline = None
		self._countdown_secs = 0
		self._game_secs_remaining = default_secs
		mins, secs = divmod(default_secs, 60)
		self.timer_lbl.setText(f"{mins}:{secs:02d}")
		# optional later: clear feed/totals if you want a fresh HUD each time
		# self.feed.clear()
		# self.red_total.setText("Red: 0"); self.green_total.setText("Green: 0")
		# self._leader = None

	def beginCountdownThenStart(self, secs:int = 5, game_length_secs:int = 6*60 + 30):
		"""Show a big N..3..2..1 overlay, then start the main match timer."""
		self.reset_to_idle(default_secs=game_length_secs)
		self.phase = Phase.COUNTDOWN
		self._game_secs_remaining = game_length_secs
	
		self._countdown_secs = max(0, int(secs))
		if self._countdown_secs == 0:
			self._start_match()
			return
	
		self._countdown_deadline = time.monotonic() + self._countdown_secs
		self.countdownLabel.setText(str(self._countdown_secs))
		self.countdownLabel.show()
		self._countdown_timer.start()  # interval 200 ms (set in _install_timers)

	def _tick_countdown(self):
		if self._countdown_deadline is None:
			return
		remaining = max(0, int(math.ceil(self._countdown_deadline - time.monotonic())))
		if remaining != self._countdown_secs:
			self._countdown_secs = remaining
			if remaining <= 0:
				self.countdownLabel.hide()
				self._countdown_timer.stop()
				self._countdown_deadline = None
				self._start_match()
			else:
				self.countdownLabel.setText(str(self._countdown_secs))
 

	def _start_match(self):
		self.phase = Phase.RUNNING
		self.gameStarted.emit()
		self._game_deadline = time.monotonic() + self._game_secs_remaining
		self._update_timer_label()
		self._game_timer.start()

	def _tick_game(self):
		if self._game_deadline is None:
			return
		remaining = max(0, int(math.ceil(self._game_deadline - time.monotonic())))
		if remaining != self._game_secs_remaining:
			self._game_secs_remaining = remaining
			self._update_timer_label()
			if remaining <= 0:
				self._game_timer.stop()
				self._game_deadline = None
				self.phase = Phase.ENDED
				self.gameEnded.emit()

	def _update_timer_label(self):
		mins, secs = divmod(max(0, self._game_secs_remaining), 60)
		self.timer_lbl.setText(f"{mins}:{secs:02d}")
