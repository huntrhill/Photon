from PyQt5 import QtWidgets, QtCore, QtGui
import os

class SplashScreen(QtWidgets.QWidget):
    def __init__(self, parent=None, assets_dir=""):
        super().__init__(parent)
        self.assets_dir = assets_dir
        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(24, 24, 24, 24)

        lbl = QtWidgets.QLabel(alignment=QtCore.Qt.AlignCenter)
        p = os.path.join(self.assets_dir, "images", "logo.jpg")
        if os.path.exists(p):
            pix = QtGui.QPixmap(p)
            lbl.setPixmap(pix.scaledToHeight(320, QtCore.Qt.SmoothTransformation))
        else:
            lbl.setText("Photon Laser Tag")
            lbl.setStyleSheet("font-size:36px; font-weight:600; color: #eee;")
        v.addWidget(lbl)

        sub = QtWidgets.QLabel("Preparing arena…", alignment=QtCore.Qt.AlignCenter)
        sub.setStyleSheet("color:#999; margin-top:12px;")
        v.addWidget(sub)

    def start(self):
        # after 3 seconds, go to Entry screen
        QtCore.QTimer.singleShot(3000, lambda: self.parent().setCurrentIndex(1))

