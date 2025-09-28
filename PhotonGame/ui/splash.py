from PyQt5 import QtWidgets, QtCore, QtGui
import os

class SplashScreen(QtWidgets.QWidget):
    def __init__(self, parent=None, assets_dir=""):
        super().__init__(parent)
        self.assets_dir = assets_dir

        self.v = QtWidgets.QVBoxLayout(self)
        self.v.setContentsMargins(24, 24, 24, 24)

        self.logo = QtWidgets.QLabel(alignment=QtCore.Qt.AlignCenter)
        self.logo.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.logo.setScaledContents(True)

        p = os.path.join(self.assets_dir, "images", "logo.jpg")
        if os.path.exists(p):
            self._pix = QtGui.QPixmap(p)
            self.logo.setPixmap(self._pix)
        else:
            self.logo.setText("Photon Laser Tag")
            self.logo.setStyleSheet("font-size:36px; font-weight:600; color:#eee;")
            self._pix = None

        self.v.addWidget(self.logo, 1)

        sub = QtWidgets.QLabel("Preparing arena…", alignment=QtCore.Qt.AlignCenter)
        sub.setStyleSheet("color:#999; margin-top:12px;")
        self.v.addWidget(sub, 0)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._pix:
            # keep aspect ratio while using most of the height
            target = self.logo.size()
            scaled = self._pix.scaled(target, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.logo.setPixmap(scaled)

    def start(self):
        QtCore.QTimer.singleShot(3000, lambda: self.parent().setCurrentIndex(1))
