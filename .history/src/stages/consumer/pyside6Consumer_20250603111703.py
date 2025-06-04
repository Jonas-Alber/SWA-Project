from .abcConsumer import AbcConsumer
import os
from PIL import Image
import numpy as np
from PySide6 import QtWidgets, QtGui
from PIL.ImageQt import ImageQt
import sys

class PySide6Consumer(AbcConsumer):
    def process(self, image: Image) -> Image:
        # Convert PIL Image to a Qt image
        qimage = ImageQt(image)
        pixmap = QtGui.QPixmap.fromImage(qimage)

        # Create or reuse the QApplication
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

        # Display the image in a QLabel
        label = QtWidgets.QLabel()
        label.setPixmap(pixmap)
        label.setWindowTitle("Empfangenes Bild")
        label.show()

        # Start the event loop (blocks until all windows are closed)
        app.exec()

        return image
