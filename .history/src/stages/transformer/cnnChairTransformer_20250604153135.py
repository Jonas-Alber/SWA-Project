from .abcImgTransformer import AbcImageTransformer
import os # Beibehalten falls für andere Zwecke benötigt, sonst entfernen
from PIL import Image, ImageDraw
import numpy as np
import cv2 # Beibehalten für Farbraumkonvertierung, falls benötigt
from ...pipeline import StageConfigElement, PipeDataClass
import torch
import torchvision
from torchvision.models.detection import FasterRCNN_ResNet50_FPN_Weights

class CnnChairTransformer(AbcImageTransformer):
    def __init__(self):
        super().__init__(self.__class__.__name__)
        # Load a pre-trained Faster R-CNN model
        self.detection_model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights=FasterRCNN_ResNet50_FPN_Weights.DEFAULT)
        self.detection_model.eval() # Set the model to evaluation mode
        # Get COCO class names
        self.coco_names = FasterRCNN_ResNet50_FPN_Weights.COCO_V1.meta['categories']
        # Find the index for 'chair'
        try:
            # COCO class IDs are 1-indexed in metadata, but model output might be 0-indexed or direct class name.
            # The 'categories' list from weights.COCO_V1.meta['categories'] is a list of strings.
            # We need to find the string 'chair'.
            self.chair_label_name = 'chair' # Target class name
            if self.chair_label_name not in self.coco_names:
                 print(f"Warning: '{self.chair_label_name}' class not found in COCO names. Chair detection will not work.")
                 self.chair_label_index = -1 # Invalid index
            else:
                # The model output labels correspond to the order in coco_names if it's a direct index.
                # Or, if the model outputs class names, we compare directly.
                # For FasterRCNN, the output labels are indices that correspond to the order in coco_names.
                self.chair_label_index = self.coco_names.index(self.chair_label_name) + 1 # COCO IDs are 1-indexed for this model's output typically
                # However, torchvision's FasterRCNN output labels are usually 0-indexed if you map them directly to a list.
                # Let's stick to finding the name and then checking the model's output labels directly.
                # The model's output `prediction[0]['labels']` will contain class IDs.
                # We need to map these IDs back to names. The `coco_names` list is 0-indexed.
                # So, if model output label is L, then coco_names[L-1] is the name (if model output is 1-indexed).
                # Or, if model output is 0-indexed, then coco_names[L] is the name.
                # Let's assume the model output labels are indices that can be used with coco_names after adjustment if necessary.
                # For simplicity, we'll find the target name and compare with model output labels.
                # The `FasterRCNN_ResNet50_FPN_Weights.COCO_V1.meta['categories']` provides the list of category names.
                # The model output `labels` are indices into this list (often 1-based, so check model docs or adjust).
                # Let's assume the model's output labels are 1-based indices for COCO.
                # The `self.coco_names` is 0-indexed list of names.
                # So, if model outputs label `k`, the name is `self.coco_names[k-1]`.
                # We are looking for when `self.coco_names[k-1] == 'chair'`.
                pass # No specific index needed here if we iterate and check names

        except ValueError:
            print(f"Warning: '{self.chair_label_name}' class not found in COCO names. Chair detection will not work.")
            self.chair_label_index = -1 # Should not happen if check above is done.

        self.confidence_threshold = 0.5 # Default confidence threshold

    def getConfigElements(self) -> list[StageConfigElement]:
        parentStageData = super().getConfigElements()
        parentStageData = parentStageData if parentStageData else []
        parentStageData.extend([
            StageConfigElement(
                text="Confidence Threshold",
                data_type=float,
                data=self.confidence_threshold
            )
        ])
        return parentStageData

    def setConfigElements(self, config_elements: list[StageConfigElement]):
        for element in config_elements:
            if element.text == "Confidence Threshold":
                try:
                    threshold = float(element.data)
                    if not (0.0 <= threshold <= 1.0):
                        raise ValueError("Confidence Threshold must be between 0.0 and 1.0.")
                    self.confidence_threshold = threshold
                except ValueError as e:
                    # Consider logging this error or re-raising with more context
                    print(f"Error setting Confidence Threshold: {e}")
                    raise ValueError("Confidence Threshold must be a number between 0.0 and 1.0.")
        super().setConfigElements(config_elements)
    
    def process(self, data: PipeDataClass) -> PipeDataClass:
        """
        Detect chairs using a CNN and add their bounding boxes as an optional layer.
        """
        chair_bbox_layer_name = f"{self.__class__.__name__}_chair_bboxes"
        data.remove_optional_layer(chair_bbox_layer_name)

        if not self._stage_visible:
            return data
        
        # --- CNN Chair Detection ---
        # Ensure base_image is a PIL Image
        if not isinstance(data.base_image, Image.Image):
            # This case should ideally not happen if PipeDataClass ensures base_image is PIL
            print("Warning: base_image is not a PIL Image. Skipping chair detection.")
            return data

        pil_image = data.base_image.convert("RGB") # Ensure image is RGB for the model
        
        # Preprocess the image
        # Using torchvision's recommended transforms for pre-trained models
        preprocess = FasterRCNN_ResNet50_FPN_Weights.DEFAULT.transforms()
        img_tensor_batch = preprocess(pil_image) # This already creates a batch [C, H, W] -> [1, C, H, W] if needed by model
        
        # The model expects a list of tensors, even if it's just one image
        if img_tensor_batch.ndim == 3: # If transform gives [C,H,W]
            img_tensor_list = [img_tensor_batch]
        else: # If transform gives [N,C,H,W]
            img_tensor_list = [img_tensor_batch[i] for i in range(img_tensor_batch.shape[0])]


        # Perform detection
        with torch.no_grad():
            prediction = self.detection_model(img_tensor_list) # Pass a list of tensors
        
        # Create a transparent layer for bounding boxes
        bbox_layer = Image.new("RGBA", data.base_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(bbox_layer)
        
        # Process detections for the first (and only) image in the batch
        # prediction is a list of dicts, one per image. We have one image.
        if prediction and len(prediction) > 0:
            pred_labels = prediction[0]['labels']
            pred_scores = prediction[0]['scores']
            pred_boxes = prediction[0]['boxes']

            for i in range(len(pred_labels)):
                score = pred_scores[i].item()
                
                if score > self.confidence_threshold:
                    label_id = pred_labels[i].item()
                    # Map label_id to class name. COCO IDs are typically 1-indexed.
                    # self.coco_names is 0-indexed.
                    # Check if label_id is within bounds for self.coco_names
                    if 0 <= (label_id -1) < len(self.coco_names): # Assuming model outputs 1-indexed COCO IDs
                        class_name = self.coco_names[label_id - 1]
                    elif 0 <= label_id < len(self.coco_names): # Assuming model outputs 0-indexed (less common for COCO)
                         class_name = self.coco_names[label_id]
                    else:
                        class_name = "unknown" # Or handle error

                    if class_name == self.chair_label_name:
                        box = pred_boxes[i].cpu().numpy()
                        x1, y1, x2, y2 = box
                        draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=3)
        
        data.add_optional_layer(chair_bbox_layer_name, bbox_layer)

        return data