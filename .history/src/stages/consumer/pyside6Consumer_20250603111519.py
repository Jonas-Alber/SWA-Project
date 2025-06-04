from .abcConsumer import AbcConsumer
import os
from PIL import Image
import numpy as np

class LoadPngStage(AbcConsumer):
    def process(self, image:Image)-> Image:
        ...
