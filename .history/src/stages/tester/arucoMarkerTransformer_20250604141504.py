# filepath: src/stages/load_csv_stage.py
from .abcImgTransformer import AbcImageTester
import os
from PIL import Image
import numpy as np
import cv2
from ...pipeline import Stage, StageConfigElement, PipeDataClass
from cv2 import aruco

class ArucoMarkerWallLineTester(AbcImageTester):
    def __init__(self):
        # draw vertical/horizontal guide lines instead of overlaying a poster
        self._draw_vertical = True
        self._draw_horizontal = True

    def getConfigElements(self) -> list[StageConfigElement]:
        return [
            StageConfigElement(
                text="Vertical Prediction Lines",
                data_type=bool,
                data=self._draw_vertical
            ),
            StageConfigElement(
                text="Horizontal Prediction Lines",
                data_type=bool,
                data=self._draw_horizontal
            )
        ]

    def setConfigElements(self, config_elements: list[StageConfigElement]):
        for element in config_elements:
            if element.text == "Vertical Prediction Lines":
                self._draw_vertical = bool(element.data)
            elif element.text == "Horizontal Prediction Lines":
                self._draw_horizontal = bool(element.data)
        return super().setConfigElements(config_elements)

    def process(self, image: Image) -> Image:
        # convert PIL→BGR
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # 1) Graustufen, Glätten, Canny-Kantendetektion
        gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur    = cv2.GaussianBlur(gray, (5, 5), 1.5)
        edges   = cv2.Canny(blur, 50, 150)

        # 2) Linien mit probabilistischem Hough-Transform finden
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=100,
            minLineLength=50,
            maxLineGap=10
        )

        # 3) nach Vertikal/Horizontalfiltern und zeichnen
        if lines is not None:
            for x1, y1, x2, y2 in lines[:, 0]:
                # Winkel in Grad berechnen
                angle = abs(np.degrees(np.arctan2((y2 - y1), (x2 - x1))))
                # vertikale Linien ~90°? horizontale ~0°?
                if self._draw_vertical and abs(angle - 90) < 10:
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                if self._draw_horizontal and angle < 10:
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # zurück zu PIL
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)
