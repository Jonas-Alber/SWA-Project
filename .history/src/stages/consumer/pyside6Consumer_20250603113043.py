from .abcConsumer import AbcConsumer
import os
from PIL import Image, ImageOps
import numpy as np
from PySide6 import QtWidgets, QtGui
from PIL.ImageQt import ImageQt
import sys
from PySide6 import QtCore, QtWidgets, QtGui


class ImageLabel(QtWidgets.QLabel):
    def __init__(self, pixmap: QtGui.QPixmap, parent=None):
        super().__init__(parent)
        self._orig = pixmap
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setStyleSheet("background-color: black;")

    def resizeEvent(self, event):
        scaled = self._orig.scaled(
            self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )
        self.setPixmap(scaled)
        super().resizeEvent(event)


class PySide6Consumer(AbcConsumer):
    def process(self, image: Image) -> Image:
        # fix EXIF orientation so it won't rotate unexpectedly
        image = ImageOps.exif_transpose(image)

        # Create or reuse the QApplication
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

        # Convert PIL Image to a Qt image
        qimage = ImageQt(image)
        pixmap = QtGui.QPixmap.fromImage(qimage)

        # Prepare main window and custom label
        window = QtWidgets.QMainWindow()
        window.setWindowTitle("Empfangenes Bild")
        label = ImageLabel(pixmap, window)
        window.setCentralWidget(label)
        window.resize(800, 600)  # Startgröße, kann der Benutzer ändern
        window.show()

        # Start the event loop (blocks until all windows are closed)
        app.exec()

        return image


class PySide6WidgetConsumer(QtWidgets.QWidget, AbcConsumer):
    def __init__(self, image: Image, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Empfangenes Bild")
        self._orig = None

        # Label zum Anzeigen des Bildes
        self.label = ImageLabel(QtGui.QPixmap(), self)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Bild direkt beim Erstellen rendern
        self.process(image)

    def process(self, image: Image) -> Image:
        # EXIF-Orientierung korrigieren
        image = ImageOps.exif_transpose(image)

        # in QPixmap umwandeln und im Label setzen
        qimage = ImageQt(image)
        pixmap = QtGui.QPixmap.fromImage(qimage)
        self._orig = pixmap
        self.label._orig = pixmap
        self.label.setPixmap(
            pixmap.scaled(
                self.label.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
        )
        return image
