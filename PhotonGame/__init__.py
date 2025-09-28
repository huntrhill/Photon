import os
from PyQt5 import QtWidgets
from PhotonGame.ui.splash import SplashScreen
from PhotonGame.ui.entry  import EntryScreen
from PhotonGame.ui.game   import GameScreen

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

def build_main_window(ctrl):
    """
    Creates the stacked UI: 0 = splash, 1 = entry, 2 = game
    Returns: (stacked, splash, entry, game, ASSETS_DIR)
    """
    stacked = QtWidgets.QStackedWidget()
    splash  = SplashScreen(stacked, assets_dir=ASSETS_DIR)
    entry   = EntryScreen(stacked, assets_dir=ASSETS_DIR)
    game    = GameScreen(stacked, assets_dir=ASSETS_DIR)

    stacked.addWidget(splash)
    stacked.addWidget(entry)
    stacked.addWidget(game)

    stacked.setWindowTitle("Photon Laser Tag")
    stacked.resize(1024, 640)
    stacked.show()

    return stacked, splash, entry, game, ASSETS_DIR
