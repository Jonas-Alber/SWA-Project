from dataclasses import dataclass, field
from PIL import Image
import numpy as np
from typing import List, Tuple, Optional

@dataclass
class PipeDataClass:
    base_image: Image.Image  # Das Bild mit allen permanenten Änderungen
    optional_layers: List[Image.Image] = field(default_factory=list)

    def add_optional_layer(self, layer_image: Image.Image):
        """Füge eine neue optionale Ebene hinzu."""
        self.optional_layers.append(layer_image)

    def merge_layers(self) -> Image.Image:
        """Gibt ein zusammengesetztes Bild zurück mit allen optionalen Ebenen."""
        # convert base_image if it's a numpy array
        base = self.base_image
        result = base.copy().convert("RGBA")

        for layer in self.optional_layers:
            img = layer
            if isinstance(img, np.ndarray):
                img = Image.fromarray(img)
            result = Image.alpha_composite(result, img.convert("RGBA"))
        return result

    def get_layer_by_id(self, layer_id: int) -> Optional[Image.Image]:
        """
        Gibt die optionale Ebene mit der angegebenen ID zurück.
        Liefert None, falls die ID ungültig ist.
        """
        if 0 <= layer_id < len(self.optional_layers):
            return self.optional_layers[layer_id]
        return None
