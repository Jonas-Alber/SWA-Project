from dataclasses import dataclass, field
from PIL import Image
import numpy as np
from typing import List, Tuple, Optional

@dataclass
class NamedLayer:
    name: str
    image: Image.Image

@dataclass
class PipeDataClass:
    base_image: Image.Image  # Das Bild mit allen permanenten Änderungen
    edit_baseImage: Image.Image = None
    optional_layers: List[NamedLayer] = field(default_factory=list)
    
    @property
    def base_image(self) -> Image.Image:
        """Gibt die Größe des Basisbildes zurück."""
        if(self.edit_baseImage is not None):
            return self.edit_baseImage
        return self.base_image
    
    @base_image.setter
    def base_image(self, image: Image.Image):
        """Setzt das Basisbild."""
        if not isinstance(image, Image.Image):
            raise TypeError("base_image must be a PIL Image.")
        self.base_image = image.convert("RGBA")
        

    def add_optional_layer(self, name: str, layer_image: Image.Image):
        """Füge eine neue optionale Ebene mit Namen hinzu."""
        self.optional_layers.append(NamedLayer(name=name, image=layer_image))
        

    def remove_optional_layer(self, name: str):
        """Entfernt eine optionale Ebene anhand ihres Namens."""
        self.optional_layers = [layer for layer in self.optional_layers if layer.name != name]

    def clear_filter_beggining_at_index(self, index: int):
        if index < 0:
            index = 0
        del self.optional_layers[index:]

    def merge_layers(self) -> Image.Image:
        """Gibt ein zusammengesetztes Bild zurück mit allen optionalen Ebenen."""
        result = self.base_image.copy().convert("RGBA")
        for named in self.optional_layers:
            img = named.image
            if isinstance(img, np.ndarray):
                img = Image.fromarray(img)
            result = Image.alpha_composite(result, img.convert("RGBA"))
        return result

    def get_layer_by_id(self, layer_id: int) -> Optional[NamedLayer]:
        """
        Gibt die optionale Ebene (mit Namen und Bild) zurück.
        Liefert None, falls die ID ungültig ist.
        """
        if 0 <= layer_id < len(self.optional_layers):
            return self.optional_layers[layer_id]
        return None
