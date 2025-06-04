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
        super().__init__(self.__class__.__name__)
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
        parentStageData = [StageConfigElement(text="Visible", data_type=str, data=self._stage_visible)]
        parentStageData = parentStageData if parentStageData else []
        parentStageData.extend([StageConfigElement(
                text="Poster Image",
                data_type=str,
                data=""
            ),
            StageConfigElement(
                text="Poster Scale",
                data_type=float,
                data=self._poster_scale
            )])
        return parentStageData

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

    def process(self, data: PipeDataClass) -> PipeDataClass:
        """
        Detect an ArUco marker in data.base_image and warp the poster onto it.
        Instead of compositing, the warped poster is stored as a new layer in data.layers.
        """
        # 1) Convert input PIL image to OpenCV BGR
        if(self._stage_visible==False): return data
        frame = cv2.cvtColor(np.array(data.base_image), cv2.COLOR_RGB2BGR)
        poster_np = cv2.cvtColor(np.array(self._poster_image), cv2.COLOR_RGB2BGR)

        # 2) Prepare scaled poster corners
        h_p, w_p = poster_np.shape[:2]
        poster_corners = np.array([[0, 0], [w_p, 0], [w_p, h_p], [0, h_p]], dtype=np.float32)
        center = poster_corners.mean(axis=0)
        sw, sh = w_p / self._poster_scale, h_p / self._poster_scale
        scaled_corners = np.array([
            [center[0] - sw, center[1] - sh],
            [center[0] + sw, center[1] - sh],
            [center[0] + sw, center[1] + sh],
            [center[0] - sw, center[1] + sh]
        ], dtype=np.float32)

        # 3) Detect ArUco markers
        aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_100)
        params = aruco.DetectorParameters()
        detector = aruco.ArucoDetector(aruco_dict, params)
        corners, ids, _ = detector.detectMarkers(frame)

        # 4) If no marker, return unchanged
        if ids is None or len(corners) == 0:
            return data

        # 5) Compute perspective transform & warp poster
        dst = corners[0][0].astype(np.float32)
        M = cv2.getPerspectiveTransform(scaled_corners, dst)
        warped = cv2.warpPerspective(poster_np, M, (frame.shape[1], frame.shape[0]))

        # 6) Convert warped BGR -> PIL.Image
        warped_rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
        poster_layer = Image.fromarray(warped_rgb)

        # 7) Attach as new layer in the PipeDataClass
        data.add_optional_layer(poster_layer)

        return data
