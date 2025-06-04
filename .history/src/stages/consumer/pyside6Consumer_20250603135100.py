from .abcConsumer import AbcConsumer
import os
from PIL import Image, ImageOps
import numpy as np
from PySide6 import QtWidgets, QtGui
from PIL.ImageQt import ImageQt
import sys
from PySide6 import QtCore, QtWidgets, QtGui
import abc
from PySide6.QtWidgets import QSizePolicy

# Metaclass combining QWidget’s metaclass with ABCMeta to avoid conflicts
class CombinedMeta(type(QtWidgets.QWidget), abc.ABCMeta):
    pass


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
class PySide6WidgetConsumer(QtWidgets.QWidget, AbcConsumer, metaclass=CombinedMeta):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Empfangenes Bild")

        # Leeren Canvas erzeugen (800x600, schwarzer Hintergrund)
        empty_pixmap = QtGui.QPixmap(800, 600)
        empty_pixmap.fill(QtGui.QColor("black"))
        self._orig = empty_pixmap
        # allow the widget (and its ImageLabel child) to expand and fill all available space
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Label zum Anzeigen des Bildes (startet mit leerem Canvas)
        self.label = ImageLabel(self._orig, self)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.label)
        self.setLayout(layout)
        
    def execute(self, image: Image) -> Image:
        """
        Process the image and display it in the widget.
        
        Args:
            image: The PIL Image to be processed and displayed.
        
        Returns:
            The processed image (same as input).
        """
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
