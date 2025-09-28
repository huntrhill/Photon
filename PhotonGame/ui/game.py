from PyQt5 import QtWidgets, QtCore, QtGui
import os

class GameScreen(QtWidgets.QWidget):
    backRequested = QtCore.pyqtSignal()

    def __init__(self, parent=None, assets_dir=""):
        super().__init__(parent)
        self.assets_dir = assets_dir
        self._base_icon = None
        p = os.path.join(self.assets_dir, "images", "baseicon.jpg")
        if os.path.exists(p):
            self._base_icon = QtGui.QIcon(p)
        self._build_ui()

    def _build_ui(self):
        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(12,12,12,12)
        v.setSpacing(8)

        # Top: timer + team totals
        top = QtWidgets.QHBoxLayout()
        self.timer_lbl = QtWidgets.QLabel("6:00", alignment=QtCore.Qt.AlignCenter)
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

        # Flash leader
        self._leader = None
        self._flash_on = False
        self._flash_timer = QtCore.QTimer(self)
        self._flash_timer.timeout.connect(self._pulse)
        self._flash_timer.start(500)

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
    def refresh(self, state, seconds_left:int):
        # Timer
        mins, secs = seconds_left // 60, seconds_left % 60
        self.timer_lbl.setText(f"{mins}:{secs:02d}")

        # Totals
        red_total = sum(s for pid,s in state.score.items() if state.team.get(pid) == "red")
        green_total = sum(s for pid,s in state.score.items() if state.team.get(pid) == "green")
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

    def _fill_team_table(self, table, state, team):
        rows = [(pid, state.codename.get(pid, ""), state.score.get(pid, 0))
                for pid,t in state.team.items() if t == team]
        rows.sort(key=lambda x: x[2], reverse=True)  # by score desc
        table.setRowCount(len(rows))
        for r,(pid,name,score) in enumerate(rows):
            table.setItem(r, 0, QtWidgets.QTableWidgetItem(str(pid)))
            name_item = QtWidgets.QTableWidgetItem(name)
            if pid in state.base_icon and self._base_icon is not None:
                name_item.setIcon(self._base_icon)
            table.setItem(r, 1, name_item)
            table.setItem(r, 2, QtWidgets.QTableWidgetItem(str(score)))

    def _pulse(self):
        # Flash the label of the leader
        lab = self.red_total if self._leader == "red" else (self.green_total if self._leader == "green" else None)
        if not lab:
            return
        self._flash_on = not self._flash_on
        if lab is self.red_total:
            lab.setStyleSheet("font-weight:bold; color: red;" if self._flash_on else "font-weight:bold; color: darkred;")
        else:
            lab.setStyleSheet("font-weight:bold; color: green;" if self._flash_on else "font-weight:bold; color: darkgreen;")

