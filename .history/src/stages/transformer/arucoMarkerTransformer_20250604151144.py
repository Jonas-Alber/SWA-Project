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
        parentStageData = super().getConfigElements()
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

        # 1. Originalbild aus PipeDataClass holen und in OpenCV-Format konvertieren
        img = data.base_image  # erwartet ein PIL.Image
        orig = np.array(img)
        if img.mode == 'RGB':
            orig = orig[..., ::-1]  # RGB -> BGR
        elif img.mode == 'RGBA':
            orig = orig[..., [2, 1, 0, 3]]  # RGBA -> BGRA
        h_img, w_img = orig.shape[:2]

        # 2. ArUco-Marker erkennen
        gray = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY)
        dictionary = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
        params = aruco.DetectorParameters_create()
        corners, ids, _ = aruco.detectMarkers(gray, dictionary, parameters=params)
        if not corners:
            return data  # kein Marker gefunden

        # Wir nehmen den ersten Marker
        c = corners[0][0].astype(np.float32)  # Form: (4,2)
        center = c.mean(axis=0)
        offsets = c - center
        dst_pts = (center + offsets * self._poster_scale).astype(np.float32)

        # 3. Quell-Punkte (Poster-Ecken) definieren
        w_p, h_p = self._poster_image.size
        src_pts = np.array([[0, 0], [w_p, 0], [w_p, h_p], [0, h_p]], dtype=np.float32)

        # 4. Poster-Bild in BGRA konvertieren
        poster_rgba = self._poster_image.convert('RGBA')
        poster_arr = np.array(poster_rgba)[..., [2, 1, 0, 3]]  # RGBA -> BGRA

        # 5. Homographie berechnen und Poster in Overlay einzeichnen
        overlay = np.zeros((h_img, w_img, 4), dtype=np.uint8)
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        cv2.warpPerspective(
            poster_arr,
            M,
            (w_img, h_img),
            dst=overlay,
            borderMode=cv2.BORDER_TRANSPARENT
        )

        # 6. Originalbild nach BGRA konvertieren
        orig_bgra = (
            cv2.cvtColor(orig, cv2.COLOR_BGR2BGRA)
            if orig.ndim == 3 else orig
        )

        # 7. Alpha-Blending Overlay auf Original
        alpha = overlay[..., 3:] / 255.0
        combined = orig_bgra.copy()
        combined[..., :3] = (overlay[..., :3] * alpha + combined[..., :3] * (1 - alpha)).astype(np.uint8)
        combined[..., 3] = np.maximum(combined[..., 3], overlay[..., 3])

        # 8. Zurück zu PIL und speichern
        combined_rgba = cv2.cvtColor(combined, cv2.COLOR_BGRA2RGBA)
        data.image = Image.fromarray(combined_rgba)
        return data

