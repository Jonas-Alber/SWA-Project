# filepath: src/stages/load_csv_stage.py
from .abcImgTransformer import AbcImageTransformer
import os
from PIL import Image
import numpy as np
import cv2
from ...pipeline import StageConfigElement, PipeDataClass
from cv2 import aruco

class ArucoMarkerTransformer(AbcImageTransformer):
    def __init__(self, poster_image: Image):
        """Args:
            poster_image (str or PIL.Image): Path or loaded poster image.
        """
        # default scale
        self._poster_scale = 5.0
        self._poster_image = (
            poster_image
            if isinstance(poster_image, Image.Image)
            else self._loadDisplayImage(poster_image)
        )

    def _loadDisplayImage(self, image: str):
        """Load the poster image from a file path."""
        if not os.path.exists(image):
            raise FileNotFoundError(f"Poster image not found at {image}")
        img = Image.open(image).convert("RGB")
        self._poster_image = img
        return img

    def getConfigElements(self) -> list[StageConfigElement]:
        return [
            StageConfigElement(
                text="Poster Image",
                data_type=str,
                data=""
            ),
            StageConfigElement(
                text="Poster Scale",
                data_type=float,
                data=self._poster_scale
            )
        ]

    def setConfigElements(self, config_elements: list[StageConfigElement]):
        for element in config_elements:
            if element.text == "Poster Image":
                if element.data and isinstance(element.data, str) and element.data!="":
                    self._loadDisplayImage(element.data)
            elif element.text == "Poster Scale":
                try:
                    scale = float(element.data)
                    if scale <= 0:
                        raise ValueError()
                except Exception:
                    raise ValueError("Poster Scale must be a positive number.")
                self._poster_scale = scale
        return super().setConfigElements(config_elements)

    def process(self, image: PipeDataClass) -> Image:
        # Convert input PIL image to OpenCV BGR
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        poster_np = cv2.cvtColor(np.array(self._poster_image), cv2.COLOR_RGB2BGR)

        # Use configured poster scale
        poster_scale = self._poster_scale
        y_offset = 0
        h_p, w_p = poster_np.shape[:2]

        # Original poster corners
        poster_corners = np.array([
            [0, 0],
            [w_p, 0],
            [w_p, h_p],
            [0, h_p]
        ], dtype=np.float32)

        # Center & scaled poster corners
        center = poster_corners.mean(axis=0)
        sw, sh = w_p / poster_scale, h_p / poster_scale
        scaled_poster_corners = np.array([
            [center[0] - sw, center[1] - sh + y_offset],
            [center[0] + sw, center[1] - sh + y_offset],
            [center[0] + sw, center[1] + sh + y_offset],
            [center[0] - sw, center[1] + sh + y_offset]
        ], dtype=np.float32)

        # Detect ArUco markers
        aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_100)
        params = aruco.DetectorParameters()
        detector = aruco.ArucoDetector(aruco_dict, params)
        corners, ids, _ = detector.detectMarkers(frame)

        if ids is None or len(corners) == 0:
            # Rotate original if no marker found
            rotated_frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            rotated_rgb = cv2.cvtColor(rotated_frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rotated_rgb)

        dst = corners[0][0].astype(np.float32)

        # Warp poster
        M = cv2.getPerspectiveTransform(scaled_poster_corners, dst)
        warped_poster = cv2.warpPerspective(poster_np, M, (frame.shape[1], frame.shape[0]))

        # Composite
        transformed_corners = cv2.perspectiveTransform(poster_corners.reshape(-1, 1, 2), M)
        pts = transformed_corners.reshape(4, 2).astype(np.int32)
        mask = np.zeros_like(frame)
        cv2.fillPoly(mask, [pts], (255, 255, 255))
        inv_mask = cv2.bitwise_not(mask)
        bg = cv2.bitwise_and(frame, inv_mask)
        result = cv2.bitwise_or(bg, warped_poster)

        # Rotate result 90° clockwise only if a poster was placed
        if ids is not None and len(corners) > 0:
            result = cv2.rotate(result, cv2.ROTATE_90_CLOCKWISE)

        # Back to PIL
        result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        return Image.fromarray(result_rgb)
