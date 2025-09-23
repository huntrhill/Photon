from PyQt5 import QtWidgets, QtCore, QtGui
import os
from PhotonGame.db import get_player, add_player

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

def build_main_window(ctrl):
    # Stacked widget: 0 splash, 1 entry, 2 game
    stacked = QtWidgets.QStackedWidget()

    splash = SplashScreen(stacked)
    entry  = EntryScreen(stacked)
    game   = GameScreen(stacked)

    stacked.addWidget(splash)
    stacked.addWidget(entry)
    stacked.addWidget(game)

    stacked.setWindowTitle("Photon Laser Tag")
    stacked.resize(1024, 640)
    stacked.show()
    return stacked, splash, entry, game, ASSETS_DIR

class SplashScreen(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        v = QtWidgets.QVBoxLayout(self)
        lbl = QtWidgets.QLabel(alignment=QtCore.Qt.AlignCenter)
        # Try to load assets/logo.jpg; fallback to text
        p = os.path.join(ASSETS_DIR, "logo.jpg")
        if os.path.exists(p):
            pix = QtGui.QPixmap(p)
            lbl.setPixmap(pix.scaledToHeight(300, QtCore.Qt.SmoothTransformation))
        else:
            lbl.setText("Photon Laser Tag")
            lbl.setStyleSheet("font-size:32px;")
        v.addWidget(lbl)

    def start(self):
        QtCore.QTimer.singleShot(3000, lambda: self.parent().setCurrentIndex(1))

class EntryScreen(QtWidgets.QWidget):
    addPlayerRequested = QtCore.pyqtSignal(int, object, int, str) # pid, codename|None, eqid, team
    startRequested = QtCore.pyqtSignal()
    clearRequested = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        self.id_edit  = QtWidgets.QLineEdit()
        self.name_edit= QtWidgets.QLineEdit()  # only used if new player
        self.eq_edit  = QtWidgets.QLineEdit()
        self.red_radio= QtWidgets.QRadioButton("Red"); self.green_radio= QtWidgets.QRadioButton("Green")
        self.red_radio.setChecked(True)
        team_h = QtWidgets.QHBoxLayout(); team_h.addWidget(self.red_radio); team_h.addWidget(self.green_radio)

        form.addRow("Player ID (int):", self.id_edit)
        form.addRow("Codename (if new):", self.name_edit)
        form.addRow("Equipment ID (int):", self.eq_edit)
        form.addRow("Team:", QtWidgets.QWidget().setLayout(team_h) if False else None)
        # workaround for form row with custom layout:
        team_w = QtWidgets.QWidget(); team_w.setLayout(team_h); form.addRow("Team:", team_w)

        layout.addLayout(form)

        # Rosters
        rosters = QtWidgets.QHBoxLayout()
        self.red_list   = QtWidgets.QTableWidget(0, 2); self.red_list.setHorizontalHeaderLabels(["ID","Codename"])
        self.green_list = QtWidgets.QTableWidget(0, 2); self.green_list.setHorizontalHeaderLabels(["ID","Codename"])
        for t in (self.red_list, self.green_list):
            t.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
            t.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        rosters.addWidget(QtWidgets.QGroupBox("Red", parent=self, layout=QtWidgets.QVBoxLayout()))
        rosters.itemAt(0).widget().layout().addWidget(self.red_list)
        rosters.addWidget(QtWidgets.QGroupBox("Green", parent=self, layout=QtWidgets.QVBoxLayout()))
        rosters.itemAt(1).widget().layout().addWidget(self.green_list)
        layout.addLayout(rosters)

        btns = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("Add Player")
        self.start_btn = QtWidgets.QPushButton("Start (F5)")
        self.clear_btn = QtWidgets.QPushButton("Clear (F12)")
        btns.addWidget(self.add_btn); btns.addStretch(1); btns.addWidget(self.start_btn); btns.addWidget(self.clear_btn)
        layout.addLayout(btns)

        self.add_btn.clicked.connect(self._emit_add)
        self.start_btn.clicked.connect(self.startRequested.emit)
        self.clear_btn.clicked.connect(self.clearRequested.emit)

        # Shortcuts
        QtWidgets.QShortcut(QtGui.QKeySequence("F5"), self, activated=self.startRequested.emit)
        QtWidgets.QShortcut(QtGui.QKeySequence("F12"), self, activated=self.clearRequested.emit)

    def _emit_add(self):
        try:
            pid = int(self.id_edit.text())
            eq  = int(self.eq_edit.text())
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Invalid", "Player ID and Equipment ID must be integers.")
            return
        team = "red" if self.red_radio.isChecked() else "green"
        codename = self.name_edit.text().strip() or None
        # enforce 15 per team
        if (team=="red" and self.red_list.rowCount()>=15) or (team=="green" and self.green_list.rowCount()>=15):
            QtWidgets.QMessageBox.warning(self, "Team Full", "Max 15 players per team.")
            return
        self.addPlayerRequested.emit(pid, codename, eq, team)
        # clear only eq field for the next entry
        self.eq_edit.clear()

    def get_or_create_player(self, pid:int, codename:str|None):
        row = get_player(pid)
        if row: return row
        if not codename:
            # prompt if not provided
            codename, ok = QtWidgets.QInputDialog.getText(self, "New Player", "Enter codename:")
            if not ok or not codename.strip():
                raise ValueError("Codename required.")
        return add_player(pid, codename.strip())

    def add_to_roster(self, pid:int, codename:str, team:str):
        table = self.red_list if team=="red" else self.green_list
        r = table.rowCount(); table.insertRow(r)
        table.setItem(r,0,QtWidgets.QTableWidgetItem(str(pid)))
        table.setItem(r,1,QtWidgets.QTableWidgetItem(codename))

    def clear_rosters(self):
        self.red_list.setRowCount(0); self.green_list.setRowCount(0)

class GameScreen(QtWidgets.QWidget):
    backRequested = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        v = QtWidgets.QVBoxLayout(self)

        # top row: timer + team scores
        top = QtWidgets.QHBoxLayout()
        self.timer_lbl = QtWidgets.QLabel("6:00", alignment=QtCore.Qt.AlignCenter)
        self.timer_lbl.setStyleSheet("font-size: 28px;")
        top.addWidget(self.timer_lbl, 1)

        self.red_total = QtWidgets.QLabel("Red: 0", alignment=QtCore.Qt.AlignCenter)
        self.green_total = QtWidgets.QLabel("Green: 0", alignment=QtCore.Qt.AlignCenter)
        top.addWidget(self.red_total, 1)
        top.addWidget(self.green_total, 1)
        v.addLayout(top)

        # middle: play by play
        self.feed = QtWidgets.QListWidget()
        v.addWidget(self.feed, 2)

        # bottom: per-team tables
        bottom = QtWidgets.QHBoxLayout()
        self.red_table = QtWidgets.QTableWidget(0, 3); self.red_table.setHorizontalHeaderLabels(["ID","Codename","Score"])
        self.green_table = QtWidgets.QTableWidget(0, 3); self.green_table.setHorizontalHeaderLabels(["ID","Codename","Score"])
        for t in (self.red_table, self.green_table):
            t.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
            t.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        bottom.addWidget(QtWidgets.QGroupBox("Red", parent=self, layout=QtWidgets.QVBoxLayout()))
        bottom.itemAt(0).widget().layout().addWidget(self.red_table)
        bottom.addWidget(QtWidgets.QGroupBox("Green", parent=self, layout=QtWidgets.QVBoxLayout()))
        bottom.itemAt(1).widget().layout().addWidget(self.green_table)
        v.addLayout(bottom, 2)

        # back button
        b = QtWidgets.QPushButton("Back to Entry")
        b.clicked.connect(self.backRequested.emit)
        v.addWidget(b, 0, alignment=QtCore.Qt.AlignRight)

        # flash effect timer
        self.flash = QtCore.QTimer(self); self.flash.setInterval(500); self.flash.timeout.connect(self._pulse)
        self.flash_on = False; self.flash.start()

    def refresh(self, state, seconds_left:int):
        # Update timer label (show pre-game too)
        mins = seconds_left // 60
        secs = seconds_left % 60
        self.timer_lbl.setText(f"{mins}:{secs:02d}")

        # Team totals and tables
        red_total = sum(s for pid,s in state.score.items() if state.team.get(pid)=="red")
        green_total = sum(s for pid,s in state.score.items() if state.team.get(pid)=="green")
        self.red_total.setText(f"Red: {red_total}")
        self.green_total.setText(f"Green: {green_total}")

        self._fill_team_table(self.red_table, state, "red")
        self._fill_team_table(self.green_table, state, "green")

        # Play-by-play (append only new lines)
        # (simple approach: rewrite everything)
        self.feed.clear()
        for line in state.feed[-200:]:
            self.feed.addItem(line)

        # store winner for flashing
        self._leader = "red" if red_total>green_total else ("green" if green_total>red_total else None)

    def _fill_team_table(self, table, state, team):
        rows = [(pid, state.codename.get(pid,""), state.score.get(pid,0))
                for pid,t in state.team.items() if t==team]
        rows.sort(key=lambda x: x[2], reverse=True)  # by score desc
        table.setRowCount(len(rows))
        for r,(pid,name,score) in enumerate(rows):
            name_display = name
            if pid in state.base_icon:
                name_display = "🏰 " + name  # base icon placeholder; swap for provided jpg in your custom cell renderer if desired
            table.setItem(r,0,QtWidgets.QTableWidgetItem(str(pid)))
            table.setItem(r,1,QtWidgets.QTableWidgetItem(name_display))
            table.setItem(r,2,QtWidgets.QTableWidgetItem(str(score)))

    def _pulse(self):
        # flash the leader label
        lab = self.red_total if getattr(self,"_leader",None)=="red" else (self.green_total if getattr(self,"_leader",None)=="green" else None)
        if not lab: return
        self.flash_on = not self.flash_on
        lab.setStyleSheet("font-weight: bold; color: red;" if (lab is self.red_total and self.flash_on) else
                          "font-weight: bold; color: darkred;" if lab is self.red_total else
                          ("font-weight: bold; color: green;" if self.flash_on else "font-weight: bold; color: darkgreen;"))
