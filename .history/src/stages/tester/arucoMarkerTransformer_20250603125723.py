# filepath: src/stages/load_csv_stage.py
from .abcImgTransformer import AbcImageTester
import os
from PIL import Image
import numpy as np
import cv2
from ...pipeline.pipeline import Stage, StageConfigElement
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
        # to BGR for OpenCV
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # detect ArUco markers
        aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_100)
        params = aruco.DetectorParameters()
        detector = aruco.ArucoDetector(aruco_dict, params)
        corners, ids, _ = detector.detectMarkers(frame)

        if ids is None or len(corners) == 0:
            # rotate if no marker
            rot = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            return Image.fromarray(cv2.cvtColor(rot, cv2.COLOR_BGR2RGB))

        # take the first marker
        pts = corners[0][0].astype(int)
        # compute approx. wall line positions
        left_x   = int((pts[0][0] + pts[3][0]) / 2)
        right_x  = int((pts[1][0] + pts[2][0]) / 2)
        top_y    = int((pts[0][1] + pts[1][1]) / 2)
        bottom_y = int((pts[2][1] + pts[3][1]) / 2)

        # draw guide lines
        if self._draw_vertical:
            cv2.line(frame, (left_x, 0),       (left_x, frame.shape[0]),   (0, 0, 255), 2)
            cv2.line(frame, (right_x, 0),      (right_x, frame.shape[0]),  (0, 0, 255), 2)
        if self._draw_horizontal:
            cv2.line(frame, (0, top_y),        (frame.shape[1], top_y),    (0, 255, 0), 2)
            cv2.line(frame, (0, bottom_y),     (frame.shape[1], bottom_y), (0, 255, 0), 2)

        # rotate 90° cw and back to PIL
        out = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        return Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))
