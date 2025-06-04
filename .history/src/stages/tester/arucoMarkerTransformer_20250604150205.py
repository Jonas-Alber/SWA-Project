# filepath: src/stages/load_csv_stage.py
from .abcImgTransformer import AbcImageTester
import os
from PIL import Image
import numpy as np
import cv2
from ...pipeline import StageConfigElement, PipeDataClass
from cv2 import aruco

class ArucoMarkerWallLineTester(AbcImageTester):
    def __init__(self):
        # draw vertical/horizontal guide lines instead of overlaying a poster
        super().__init__(self.__class__.__name__)
        self._draw_vertical = True
        self._draw_horizontal = True

    def getConfigElements(self) -> list[StageConfigElement]:
        parentStageData = super().getConfigElements()
        return parentStageData + [
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

    def process(self, data: PipeDataClass) -> PipeDataClass:
        # convert PIL→BGR
        #if(self._stage_visible==False): return data
        frame = cv2.cvtColor(np.array(data.base_image), cv2.COLOR_RGB2BGR)

        # 1) Graustufen, Glätten, Canny-Kantendetektion
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur  = cv2.GaussianBlur(gray, (5, 5), 1.5)
        edges = cv2.Canny(blur, 50, 150)

        # 2) Linien mit probabilistischem Hough-Transform finden
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=100,
            minLineLength=50,
            maxLineGap=10
        )

        # Vorbereitung einer transparenten RGBA-Maske für die Linien
        h, w = edges.shape
        line_mask = np.zeros((h, w, 4), dtype=np.uint8)

        # 3) nach Vertikal/Horizontal filtern und auf die Maske zeichnen
        if lines is not None:
            for x1, y1, x2, y2 in lines[:, 0]:
                angle = abs(np.degrees(np.arctan2((y2 - y1), (x2 - x1))))
                if self._draw_vertical and abs(angle - 90) < 10:
                    # Rot mit voller Deckkraft
                    cv2.line(line_mask, (x1, y1), (x2, y2), (0, 0, 255, 255), 2)
                if self._draw_horizontal and angle < 10:
                    # Grün mit voller Deckkraft
                    cv2.line(line_mask, (x1, y1), (x2, y2), (0, 255, 0, 255), 2)

        # Maske von BGRA→RGBA und zu PIL konvertieren
        mask_rgba = cv2.cvtColor(line_mask, cv2.COLOR_BGRA2RGBA)
        line_layer = Image.fromarray(mask_rgba)

        # Optionales Layer im PipeDataClass ablegen
        data.add_optional_layer(self.__class__.__name__,line_layer)

        # Base image bleibt unverändert, kein direktes Overlay
        return data
