"""
Entry screen: keeps original starfield look, but exposes the signals + methods
that app.py expects:
  - addPlayerRequested(int pid, object codenameOrNone, int eqid, str team)
  - startRequested()
  - clearRequested()
  - get_or_create_player(pid, codenameOrNone)
  - add_to_roster(pid, codename, team)
  - clear_rosters()
"""

import random
from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QSizePolicy, QFrame, QGroupBox,
    QTableWidget, QMessageBox, QRadioButton, QFormLayout, QHeaderView, QShortcut
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPixmap, QFont, QKeySequence
from PhotonGame.db import get_player, add_player


# ---------- Starfield Background (unchanged) ----------
class Star:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.reset()

    def reset(self):
        self.x = random.randint(0, self.width)
        self.y = random.randint(0, self.height)
        self.z = random.randint(1, self.width // 2)

    def move(self, speed=5):
        self.z -= speed
        if self.z <= 0:
            self.reset()

class StarField(QWidget):
    def __init__(self, width, height, num_stars=200):
        super().__init__()
        self.setFixedSize(width, height)
        self.stars = [Star(width, height) for _ in range(num_stars)]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

        # Layout to hold tables and form
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(50, 50, 50, 50)
        self.setLayout(self.main_layout)

    def add_widget_layout(self, layout):
        self.main_layout.addLayout(layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("black"))
        painter.setPen(QColor("white"))
        width = self.width() / 2
        height = self.height() / 2
        for star in self.stars:
            sx = int((star.x - width) / star.z * 300 + width)
            sy = int((star.y - height) / star.z * 300 + height)
            painter.drawPoint(sx, sy)
            star.move()


# ---------- EntryScreen wrapper (new) ----------
class EntryScreen(QWidget):
    addPlayerRequested = pyqtSignal(int, object, int, str)  # pid, codename|None, eqid, team
    startRequested     = pyqtSignal()
    clearRequested     = pyqtSignal()

    def __init__(self, parent=None, assets_dir=""):
        super().__init__(parent)
        self.assets_dir = assets_dir
        self._build_ui()

    def _build_ui(self):
        # Starfield background container
        self.starfield = StarField(1500, 800, num_stars=220)
        root = QVBoxLayout(self)
        root.setContentsMargins(0,0,0,0)
        root.addWidget(self.starfield)

        # ---------- Left/Right team tables ----------
        def create_table(team):
            table = QTableWidget()
            table.setRowCount(0)              # dynamic rows
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["PlayerID", "Codename"])
            table.verticalHeader().setVisible(False)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setSelectionMode(QTableWidget.SingleSelection)
            table.setFixedWidth(550)
            table.setFixedHeight(650)
            table.setColumnWidth(0, 274)
            table.setColumnWidth(1, 275)
            table.setStyleSheet(
                "background-color: rgba(0, 0, 0, 0); color: white; "
                f"gridline-color: {'red' if team=='red' else 'green'};"
            )
            table.horizontalHeader().setStretchLastSection(True)
            return table

        self.red_table   = create_table("red")
        self.green_table = create_table("green")

        red_label   = QLabel("Photon Phantoms");  red_label.setAlignment(Qt.AlignCenter)
        green_label = QLabel("Quantum Warriors"); green_label.setAlignment(Qt.AlignCenter)
        red_label.setStyleSheet("color: red; font-family: Futura; font-weight: bold; font-size: 40px;")
        green_label.setStyleSheet("color: green; font-family: Futura; font-weight: bold; font-size: 40px;")

        red_layout = QVBoxLayout();   red_layout.addWidget(red_label);   red_layout.addWidget(self.red_table)
        green_layout = QVBoxLayout(); green_layout.addWidget(green_label); green_layout.addWidget(self.green_table)

        # ---------- Center form (id, codename, equipment, team, buttons) ----------
        center = QVBoxLayout()
        center.addStretch()

        # Logo
        logo_label = QLabel()
        logo_path = f"{self.assets_dir}/images/logo.jpg"
        pm = QPixmap(logo_path)
        if not pm.isNull():
            logo_label.setPixmap(pm.scaledToWidth(200, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        center.addWidget(logo_label)

        form = QFormLayout()
        self.id_input   = QLineEdit(); self.id_input.setPlaceholderText("Enter Player ID (integer)")
        self.name_input = QLineEdit(); self.name_input.setPlaceholderText("Codename (if new)")
        self.eq_input   = QLineEdit(); self.eq_input.setPlaceholderText("Equipment ID (integer)")
        self.id_input.setStyleSheet("font-family: Futura; background-color: #333; color: white;")
        self.name_input.setStyleSheet("font-family: Futura; background-color: #333; color: white;")
        self.eq_input.setStyleSheet("font-family: Futura; background-color: #333; color: white;")

        self.red_radio = QRadioButton("Red")
        self.green_radio = QRadioButton("Green")
        self.red_radio.setChecked(True)
        team_h = QHBoxLayout(); team_h.addWidget(self.red_radio); team_h.addWidget(self.green_radio)
        team_w = QWidget(); team_w.setLayout(team_h)

        form.addRow("Player ID:", self.id_input)
        form.addRow("Codename:", self.name_input)
        form.addRow("Equipment ID:", self.eq_input)
        form.addRow("Team:", team_w)
        center.addLayout(form)

        # Buttons
        btn_row = QHBoxLayout()
        self.lookup_btn = QPushButton("Add Player")
        self.lookup_btn.setStyleSheet("font-family: Futura; background-color: #555; color: white;")
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
        self.result_label.setStyleSheet("font-family: Futura; color: white;")
        center.addWidget(self.result_label)

        center.addStretch()

        # Wire to starfield layout (left | center | right)
        main_layout = QHBoxLayout()
        main_layout.addLayout(red_layout)
        main_layout.addLayout(center)
        main_layout.addLayout(green_layout)
        self.starfield.add_widget_layout(main_layout)

        # Wiring to app.py via signals
        self.lookup_btn.clicked.connect(self._emit_add)
        self.start_btn.clicked.connect(self.startRequested.emit)
        self.clear_btn.clicked.connect(self.clearRequested.emit)

        # Keyboard shortcuts
        QShortcut(QKeySequence("F5"),  self, activated=self.startRequested.emit)
        QShortcut(QKeySequence("F12"), self, activated=self.clearRequested.emit)

    # ---- helpers / API used by app.py ----
    def _emit_add(self):
        pid_text = self.id_input.text().strip()
        eq_text  = self.eq_input.text().strip()
        if not pid_text.isdigit() or not eq_text.isdigit():
            QMessageBox.warning(self, "Invalid", "Player ID and Equipment ID must be integers.")
            return
        pid = int(pid_text); eqid = int(eq_text)
        team = "red" if self.red_radio.isChecked() else "green"
        codename = self.name_input.text().strip() or None

        # enforce 15 per team
        table = self.red_table if team == "red" else self.green_table
        if table.rowCount() >= 15:
            QMessageBox.warning(self, "Team Full", "Max 15 players per team.")
            return

        self.addPlayerRequested.emit(pid, codename, eqid, team)
        # feedback + prep next
        self.result_label.setText(f"Queued add: Player {pid} ({'new' if codename else 'lookup'}), eq {eqid}, team {team}")
        self.eq_input.clear()

    def get_or_create_player(self, pid: int, codename: str|None):
        row = get_player(pid)
        if row:
            # normalize to (id, codename)
            if isinstance(row, dict):
                return (row.get("id"), row.get("codename"))
            return row
        # prompt only if not provided
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
