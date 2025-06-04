from dataclasses import dataclass, field
from PIL import Image
from typing import List, Tuple, Optional

@dataclass
class PipeDataClass:
    base_image: Image.Image  # Das Bild mit allen permanenten Änderungen
    optional_layers: List[Tuple[str, Image.Image]] = field(default_factory=list)
    # Tuple[str, Image.Image]: Name + Bild der optionalen Ebene

    def add_optional_layer(self, name: str, layer_image: Image.Image):
        """Füge eine neue optionale Ebene hinzu (z. B. Hilfslinien)."""
        self.optional_layers.append((name, layer_image))

    def get_layer_by_name(self, name: str) -> Optional[Image.Image]:
        """Hole eine Ebene anhand ihres Namens."""
        for n, img in self.optional_layers:
            if n == name:
                return img
        return None

    def merge_layers(self) -> Image.Image:
        """Gibt ein zusammengesetztes Bild zurück mit allen optionalen Ebenen."""
        result = self.base_image.copy().convert("RGBA")
        for _, layer in self.optional_layers:
            result = Image.alpha_composite(result, layer.convert("RGBA"))
        return result
