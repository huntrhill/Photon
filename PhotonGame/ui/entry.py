"""
Entry screen: starfield background + responsive UI.
Exposes the signals/methods app.py expects:
  - addPlayerRequested(int pid, object codenameOrNone, int eqid, str team)
  - startRequested()
  - clearRequested()
  - get_or_create_player(pid, codenameOrNone)
  - add_to_roster(pid, codename, team)
  - clear_rosters()
"""

import os, random
from typing import Optional

from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QSizePolicy, QMessageBox, QRadioButton,
    QFormLayout, QHeaderView, QShortcut, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPixmap, QKeySequence

from PhotonGame.db import get_player, add_player


# ---------- Starfield Background ----------
class Star:
	def __init__(self, width, height):
		self.width = width
		self.height = height
		self.reset()
	
	def reset(self):
		self.x = random.randint(0, self.width)
		self.y = random.randint(0, self.height)
		self.z = random.randint(1, max(2, self.width // 2))
	
	def move(self, speed=5):
		self.z -= speed
		if self.z <= 0:
			self.reset()


class StarField(QWidget):
	def __init__(self, width=0, height=0, num_stars=200):
		super().__init__()
		self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
	
		# Create stars relative to an initial guess; drawing adapts to current size.
		self.stars = [Star(1600, 900) for _ in range(num_stars)]
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.update)
		self.timer.start(30)
	
		self.main_layout = QHBoxLayout()
		self.main_layout.setContentsMargins(16, 16, 16, 16)
		self.setLayout(self.main_layout)
	
	def add_widget_layout(self, layout):
		self.main_layout.addLayout(layout)
	
	def paintEvent(self, event):
		painter = QPainter(self)
		painter.fillRect(self.rect(), QColor("black"))
		painter.setPen(QColor("white"))
	
		w = max(1, self.width())
		h = max(1, self.height())
		cx = w / 2
		cy = h / 2
		depth_scale = max(w, h) / 2
	
		for star in self.stars:
			sx = int((star.x - cx) / max(1, star.z) * (depth_scale * 0.6) + cx)
			sy = int((star.y - cy) / max(1, star.z) * (depth_scale * 0.6) + cy)
			if 0 <= sx < w and 0 <= sy < h:
				painter.drawPoint(sx, sy)
			star.move(speed=5)
			if star.z <= 0:
				star.x = random.randint(0, w)
				star.y = random.randint(0, h)
				star.z = random.randint(1, max(2, int(depth_scale)))


# ---------- EntryScreen ----------
class EntryScreen(QWidget):
	addPlayerRequested = pyqtSignal(int, object, int, str)  # pid, codename|None, eqid, team
	startRequested     = pyqtSignal()
	clearRequested     = pyqtSignal()
	
	def __init__(self, parent=None, assets_dir: str = ""):
		super().__init__(parent)
		self.assets_dir = assets_dir
		self._build_ui()
	
	def _build_ui(self):
		# Starfield container
		self.starfield = StarField(1024, 640, num_stars=220)
		root = QVBoxLayout(self)
		root.setContentsMargins(0, 0, 0, 0)
		root.addWidget(self.starfield)
	
		# ---------- Left/Right team tables ----------
		def create_table(team: str) -> QTableWidget:
			table = QTableWidget(0, 2)
			table.setHorizontalHeaderLabels(["PlayerID", "Codename"])
			table.verticalHeader().setVisible(False)
			table.setSelectionBehavior(QTableWidget.SelectRows)
			table.setSelectionMode(QTableWidget.SingleSelection)
			table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
	
			hdr = table.horizontalHeader()
			hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
			hdr.setSectionResizeMode(1, QHeaderView.Stretch)
	
			color = "red" if team == "red" else "green"
			table.setStyleSheet(
				"background-color: rgba(0,0,0,0); color: white; "
				f"gridline-color: {color};"
			)
			return table
	
		self.red_table   = create_table("red")
		self.green_table = create_table("green")
	
		red_label = QLabel("Photon Phantoms");   red_label.setAlignment(Qt.AlignCenter)
		green_label = QLabel("Quantum Warriors"); green_label.setAlignment(Qt.AlignCenter)
		red_label.setStyleSheet("color: red; font-weight: bold; font-size: 28px;")
		green_label.setStyleSheet("color: green; font-weight: bold; font-size: 28px;")
	
		red_layout = QVBoxLayout();   red_layout.addWidget(red_label);   red_layout.addWidget(self.red_table)
		green_layout = QVBoxLayout(); green_layout.addWidget(green_label); green_layout.addWidget(self.green_table)
	
		# ---------- Center form ----------
		center = QVBoxLayout()
		center.addStretch()
	
		# Logo (scaled, capped height to keep fields visible)
		logo_label = QLabel(); logo_label.setAlignment(Qt.AlignCenter)
		logo_path = os.path.join(self.assets_dir, "images", "logo.jpg")
		if os.path.isfile(logo_path):
			pm = QPixmap(logo_path)
			if not pm.isNull():
				logo_label.setPixmap(pm)
				logo_label.setScaledContents(True)
				logo_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
				logo_label.setMaximumHeight(160)
		center.addWidget(logo_label)
	
		# Inputs
		self.id_input   = QLineEdit(); self.id_input.setPlaceholderText("Enter Player ID (integer)")
		self.name_input = QLineEdit(); self.name_input.setPlaceholderText("Codename (if new)")
		self.eq_input   = QLineEdit(); self.eq_input.setPlaceholderText("Equipment ID (integer)")
		for w in (self.id_input, self.name_input, self.eq_input):
			w.setStyleSheet("background-color: #333; color: white; padding: 6px;")
			w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
	
		self.red_radio = QRadioButton("Red")
		self.green_radio = QRadioButton("Green")
		self.red_radio.setChecked(True)
		team_h = QHBoxLayout(); team_h.addWidget(self.red_radio); team_h.addWidget(self.green_radio)
		team_w = QWidget(); team_w.setLayout(team_h)
	
		form = QFormLayout()
		form.addRow("Player ID:", self.id_input)
		form.addRow("Codename:", self.name_input)
		form.addRow("Equipment ID:", self.eq_input)
		form.addRow("Team:", team_w)
		center.addLayout(form)
	
		# Buttons
		btn_row = QHBoxLayout()
		self.lookup_btn = QPushButton("Add Player")
		self.lookup_btn.setStyleSheet("background-color: #555; color: white; padding: 6px 10px;")
		self.start_btn  = QPushButton("Start (F5)")
		self.clear_btn  = QPushButton("Clear (F12)")
		btn_row.addWidget(self.lookup_btn)
		btn_row.addStretch()
		btn_row.addWidget(self.start_btn)
		btn_row.addWidget(self.clear_btn)
		center.addLayout(btn_row)
	
		# Result label
		self.result_label = QLabel("Ready")
		self.result_label.setAlignment(Qt.AlignCenter)
		self.result_label.setStyleSheet("color: #DDD; margin-top: 6px;")
		center.addWidget(self.result_label)
	
		center.addStretch()
	
		# Compose (left | center | right)
		main_layout = QHBoxLayout()
		main_layout.addLayout(red_layout,   1)
		main_layout.addLayout(center,       1)
		main_layout.addLayout(green_layout, 1)
		self.starfield.add_widget_layout(main_layout)
	
		# Signals to app.py
		self.lookup_btn.clicked.connect(self._emit_add)
		self.start_btn.clicked.connect(self.startRequested.emit)
		self.clear_btn.clicked.connect(self.clearRequested.emit)
	
		# Shortcuts
		QShortcut(QKeySequence("F5"),  self, activated=self.startRequested.emit)
		QShortcut(QKeySequence("F12"), self, activated=self.clearRequested.emit)
	
		# Optional: keep UI usable at small sizes
		self.setMinimumSize(900, 560)
	
	# ---- helpers / API used by app.py ----
	def _emit_add(self):
		pid_text = self.id_input.text().strip()
		eq_text  = self.eq_input.text().strip()
		if not pid_text.isdigit() or not eq_text.isdigit():
			QMessageBox.warning(self, "Invalid", "Player ID and Equipment ID must be integers.")
			return
		pid = int(pid_text)
		eqid = int(eq_text)
		team = "green" if pid % 2 == 0 else "red"
		print("Here")
		codename = self.name_input.text().strip() or None
		
		# enforce 15 per team
		table = self.red_table if team == "red" else self.green_table
		if table.rowCount() >= 15:
			QMessageBox.warning(self, "Team Full", "Max 15 players per team.")
			return
		
		self.addPlayerRequested.emit(pid, codename, eqid, team)
		self.result_label.setText(
			f"Queued: Player {pid} ({'new' if codename else 'lookup'}), eq {eqid}, team {team}"
		)
		self.eq_input.clear()
	
	def get_or_create_player(self, pid: int, codename: Optional[str]):
		row = get_player(pid)
		if row:
			# normalize to (id, codename)
			if isinstance(row, dict):
				return (row.get("id"), row.get("codename"))
			return row
		if not codename:
			text, ok = QInputDialog.getText(self, "New Player", "Enter codename:")
			if not ok or not text.strip():
				raise ValueError("Codename required.")
			codename = text.strip()
		row = add_player(pid, codename)
		if isinstance(row, dict):
			return (row.get("id"), row.get("codename"))
		return row
	
	def add_to_roster(self, pid: int, codename: str, team: str):
		table = self.red_table if team == "red" else self.green_table
		r = table.rowCount()
		table.insertRow(r)
		table.setItem(r, 0, QTableWidgetItem(str(pid)))
		table.setItem(r, 1, QTableWidgetItem(codename))
	
	def clear_rosters(self):
		self.red_table.setRowCount(0)
		self.green_table.setRowCount(0)
		self.result_label.setText("Cleared.")
	
