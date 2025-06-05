# filepath: src/stages/load_csv_stage.py
from .abcImgTransformer import AbcImageTransformer
import os
from PIL import Image
import numpy as np
import cv2
from ...pipeline import StageConfigElement, PipeDataClass
from cv2 import aruco
class RotateTransformer(AbcImageTransformer):
    def __init__(self, angle: float = 0.0):
        """
        Args:
            angle (float): Rotation angle in degrees.
        """
        super().__init__(self.__class__.__name__)
        self._angle = angle

    def getConfigElements(self) -> list[StageConfigElement]:
        cfg = super().getConfigElements() or []
        cfg.append(StageConfigElement(
            text="Rotation Angle",
            data_type=float,
            data=self._angle
        ))
        return cfg

    def setConfigElements(self, config_elements: list[StageConfigElement]):
        for elem in config_elements:
            if elem.text == "Rotation Angle":
                try:
                    ang = float(elem.data)
                except Exception:
                    raise ValueError("Rotation Angle must be a number.")
                self._angle = ang
        return super().setConfigElements(config_elements)

    def process(self, data: PipeDataClass) -> PipeDataClass:
        if not self._stage_visible:
            return data

        # Convert input PIL image -> OpenCV
        arr = np.array(data.base_image)
        if arr.shape[2] == 4:
            cv_img = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGRA)
        else:
            cv_img = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

        # compute rotation
        h, w = cv_img.shape[:2]
        center = (w / 2, h / 2)
        M = cv2.getRotationMatrix2D(center, self._angle, 1.0)
        rotated = cv2.warpAffine(
            cv_img, M, (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT
        )

        # back to PIL.Image
        if rotated.shape[2] == 4:
            out = cv2.cvtColor(rotated, cv2.COLOR_BGRA2RGBA)
        else:
            out = cv2.cvtColor(rotated, cv2.COLOR_BGR2RGB)
        rotated_pil = Image.fromarray(out)

        # overwrite the original image instead of adding an optional layer
        data.base_image = rotated_pil
        return data

class FlipTransformer(AbcImageTransformer):
    def __init__(self, horizontal: bool = False, vertical: bool = False):
        """
        Args:
            horizontal (bool): flip left/right
            vertical (bool): flip top/bottom
        """
        super().__init__(self.__class__.__name__)
        self._horizontal = horizontal
        self._vertical = vertical

    def getConfigElements(self) -> list[StageConfigElement]:
        cfg = super().getConfigElements() or []
        cfg.append(StageConfigElement(
            text="Flip Horizontal",
            data_type=bool,
            data=self._horizontal
        ))
        cfg.append(StageConfigElement(
            text="Flip Vertical",
            data_type=bool,
            data=self._vertical
        ))
        return cfg

    def setConfigElements(self, config_elements: list[StageConfigElement]):
        for elem in config_elements:
            if elem.text == "Flip Horizontal":
                self._horizontal = bool(elem.data)
            elif elem.text == "Flip Vertical":
                self._vertical = bool(elem.data)
        return super().setConfigElements(config_elements)

    def process(self, data: PipeDataClass) -> PipeDataClass:
        if not self._stage_visible:
            return data

        # Convert PIL image -> OpenCV
        arr = np.array(data.base_image)
        if arr.shape[2] == 4:
            cv_img = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGRA)
        else:
            cv_img = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

        # determine flip code
        if self._horizontal and self._vertical:
            code = -1
        elif self._horizontal:
            code = 1
        elif self._vertical:
            code = 0
        else:
            # no flip requested
            return data

        flipped = cv2.flip(cv_img, code)

        # Convert back to PIL.Image
        if flipped.shape[2] == 4:
            out = cv2.cvtColor(flipped, cv2.COLOR_BGRA2RGBA)
        else:
            out = cv2.cvtColor(flipped, cv2.COLOR_BGR2RGB)

        data.base_image = Image.fromarray(out)
        return data