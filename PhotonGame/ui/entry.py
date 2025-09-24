"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This is ran on my local machine, the GUI is completley done, just 
to connect to the database.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""



import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QLabel, QPushButton,QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem, QSizePolicy, QFrame
from FakeDB import FakePlayerDatabase
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QPixmap, QFont
import random


# ---------- Starfield Background ----------
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
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

        #Layout to hold tables and search bar
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(50, 50, 50, 50)
        self.setLayout(self.main_layout)
    #
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


# ---------- Player Lookup Layout ----------
def create_player_lookup_layout(db):
    # Tables
    def create_table(team):
        table = QTableWidget()
        table.setRowCount(20)
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["PlayerID", "Codename"])
        table.setStyleSheet("font-family: Futura; font-weight: bold")
        color = "red" if team == "red" else "green"
        table.setStyleSheet(f"background-color: rgba(0, 0, 0, 0); color: white; gridline-color: {color};")
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setFixedWidth(550)
        table.setFixedHeight(650)
        table.setColumnWidth(0, 274)
        table.setColumnWidth(1, 275)
        return table


    #creating seperate tables for teams
    red_table = create_table("red")
    green_table = create_table("green")

    #Team labels
    red_label = QLabel("Photon Phantoms")
    red_label.setStyleSheet("color: red; font-family: Futura; font-weight: bold;font-size: 40px;")
    red_label.setAlignment(Qt.AlignCenter)

    green_label = QLabel("Quantum Warriors")
    green_label.setStyleSheet("color: green; font-family: Futura; font-weight: bold;font-size: 40px;")
    green_label.setAlignment(Qt.AlignCenter)

    #Red layout
    red_layout = QVBoxLayout()
    red_layout.addWidget(red_label)
    red_layout.addWidget(red_table)

    #Green layout
    green_layout = QVBoxLayout()
    green_layout.addWidget(green_label)
    green_layout.addWidget(green_table)

    #Search bar
    id_input = QLineEdit()
    id_input.setPlaceholderText("Enter Player ID")
    id_input.setStyleSheet("font-family: Futura; background-color: #333; color: white;")
    search_btn = QPushButton("Lookup Player")
    search_btn.setStyleSheet("font-family: Futura; background-color: #555; color: white;")
    result_label = QLabel("Codename will appear here")
    result_label.setStyleSheet("font-family: Futura; color: white;")
    result_label.setAlignment(Qt.AlignCenter)

    #Bringing in the photon logo jpeg for the data entry screen
    logo_label = QLabel()
    pixmap = QPixmap("/Users/hunterhill/DataScience/SoftwareENG/Project/logo.jpg")  # replace with your file path
    pixmap = pixmap.scaledToWidth(200, Qt.SmoothTransformation)  # optional: scale width
    logo_label.setPixmap(pixmap)
    logo_label.setAlignment(Qt.AlignCenter)

    #layout of all the boxes
    search_layout = QVBoxLayout()
    search_layout.addStretch()
    search_layout.addWidget(logo_label)  
    search_layout.addWidget(id_input)
    search_layout.addWidget(search_btn)
    search_layout.addWidget(result_label)
    search_layout.addStretch()

    #Connecting the search button to find in the data base
    def lookup_player():
        pid_text = id_input.text()
        if not pid_text.isdigit():
            result_label.setText("Enter a valid integer ID")
            return
        pid = int(pid_text)
        codename = db.get_code_name(pid)
        if not codename:
            codename = f"Player{pid}"  # fallback if not in DB

        #Decide team even = red, odd = green
        if pid % 2 == 0:
            team_table = red_table
        else:
            team_table = green_table

        #Check if player already exists
        if is_player_in_table(team_table, pid):
            result_label.setText(f"Player {pid} is already on a team!")
            return

        #Add player to table
        add_player_to_table(team_table, pid, codename)
        result_label.setText(f"Added Player {pid}: {codename}")
    
    #either pressing button or pressing enter will search for the players ID
    search_btn.clicked.connect(lookup_player)
    id_input.returnPressed.connect(lookup_player)

    #Main horizontal layout: red | search | green
    main_layout = QHBoxLayout()
    main_layout.addLayout(red_layout)
    main_layout.addLayout(search_layout)
    main_layout.addLayout(green_layout)

    return main_layout

#function to add player automatically to the team tables
def add_player_to_table(table, pid, codename):
    for row in range(table.rowCount()):
        if table.item(row, 0) is None:  # empty row
            table.setItem(row, 0, QTableWidgetItem(str(pid)))
            table.setItem(row, 1, QTableWidgetItem(codename))
            break
#error checking to see if the player is already on a team
def is_player_in_table(table, pid):
    for row in range(table.rowCount()):
        item = table.item(row, 0)  
        if item and item.text() == str(pid):
            return True
    return False

# ---------- Run ----------
if __name__ == "__main__":
    class DummyDB:
        def get_code_name(self, pid):
            return f"Player{pid}"  # placeholder

    app = QApplication(sys.argv)
    starfield = StarField(1500, 800)

    player_layout = create_player_lookup_layout(DummyDB())
    starfield.add_widget_layout(player_layout)

    starfield.show()
    sys.exit(app.exec_())
