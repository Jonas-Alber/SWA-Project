from .abcImgTransformer import AbcImageTransformer
import os # Beibehalten falls für andere Zwecke benötigt, sonst entfernen
from PIL import Image, ImageDraw
import numpy as np
import cv2 # Beibehalten für Farbraumkonvertierung, falls benötigt
from ...pipeline import StageConfigElement, PipeDataClass
import torch
import torchvision
from torchvision.models.detection import FasterRCNN_ResNet50_FPN_Weights
from torchvision.models.detection import fasterrcnn_mobilenet_v3_large_fpn, FasterRCNN_MobileNet_V3_Large_FPN_Weights

class CnnChairTransformer(AbcImageTransformer):
    def __init__(self):
        super().__init__(self.__class__.__name__)
        # Load a pre-trained YOLOv5 model
        # You can choose other models like 'yolov5m', 'yolov5l', 'yolov5x'
        # or specify a custom path: self.detection_model = torch.hub.load('ultralytics/yolov5', 'custom', path='path/to/best.pt')
        try:
            self.detection_model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        except Exception as e:
            print(f"Error loading YOLOv5 model: {e}")
            print("Please ensure you have an internet connection for the first download,")
            print("or provide a local path to the model weights.")
            # Fallback or re-raise, depending on desired behavior
            # For now, let's allow it to proceed but it will fail in process()
            self.detection_model = None 
            self.coco_names = []

        if self.detection_model:
            self.detection_model.eval()
            self.coco_names = self.detection_model.names # YOLOv5 provides class names via .names attribute
        
        # Define target object types and their default detection status
        self.target_object_names = ["chair", "person", "car", "dog", "cat", "dining table"] # tvmonitor is often 'tv' in COCO

        # Enable detection for all target classes by default
        self.detection_targets = {name: True for name in self.target_object_names}

        # Validate that all target names are in COCO names
        if self.coco_names:
            for name in self.target_object_names:
                if name not in self.coco_names:
                    print(f"Warning: Target class '{name}' not found in YOLOv5 COCO names. Detection for this class might not work.")
        else:
            print("Warning: COCO names not available, cannot validate target object names.")


        self.confidence_threshold = 0.5 # Default confidence threshold


    def getConfigElements(self) -> list[StageConfigElement]:
        parentStageData = super().getConfigElements()
        parentStageData = parentStageData if parentStageData else []
        parentStageData.extend([
            StageConfigElement(
                text="Confidence Threshold",
                data_type=float,
                data=self.confidence_threshold
            ),
            StageConfigElement(
                text="Detection Targets",
                data_type=dict, # dict[str, bool]
                data=self.detection_targets.copy() # Pass a copy
            )
        ])
        return parentStageData

    def setConfigElements(self, config_elements: list[StageConfigElement]):
        super().setConfigElements(config_elements) # Call super first or ensure its logic is preserved
        for element in config_elements:
            if element.text == "Confidence Threshold":
                try:
                    threshold = float(element.data)
                    if not (0.0 <= threshold <= 1.0):
                        raise ValueError("Confidence Threshold must be between 0.0 and 1.0.")
                    self.confidence_threshold = threshold
                except ValueError as e:
                    print(f"Error setting Confidence Threshold: {e}")
                    # Optionally re-raise or handle as appropriate for your application
                    # raise ValueError("Confidence Threshold must be a number between 0.0 and 1.0.")
            elif element.text == "Detection Targets":
                if isinstance(element.data, dict):
                    # Update self.detection_targets based on received data
                    # Only update keys that are already defined to prevent adding arbitrary keys
                    for key, value in element.data.items():
                        if key in self.detection_targets:
                            self.detection_targets[key] = bool(value)
                        else:
                            print(f"Warning: Received unknown detection target '{key}' in config.")
                else:
                    print(f"Error: 'Detection Targets' config is not a dictionary. Received: {type(element.data)}")
    def process(self, data: PipeDataClass) -> PipeDataClass:
        """
        Detect configured objects using a YOLOv5 CNN and add their bounding boxes as an optional layer.
        """
        detected_objects_layer_name = f"{self.__class__.__name__}_detected_objects_bboxes"
        data.remove_optional_layer(detected_objects_layer_name)

        if not self._stage_visible:
            return data
        
        if not self.detection_model:
            print("Error: YOLOv5 model not loaded. Skipping object detection.")
            return data
            
        if not self.coco_names:
            print("Error: COCO names not available from YOLOv5 model. Skipping object detection.")
            return data

        # --- YOLOv5 Object Detection ---
        if not isinstance(data.base_image, Image.Image):
            print("Warning: base_image is not a PIL Image. Skipping object detection.")
            return data

        pil_image = data.base_image.convert("RGB")
        
        # YOLOv5 handles its own preprocessing when given a PIL image
        # No explicit preprocessing transform needed like with FasterRCNN

        with torch.no_grad():
            # Perform inference
            results = self.detection_model(pil_image, size=pil_image.width) # You can specify inference size, e.g., size=640
        
        bbox_layer = Image.new("RGBA", data.base_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(bbox_layer)
        
        # Process results
        # results.xyxy[0] contains detections for the first (and only) image:
        # (tensor) [xmin, ymin, xmax, ymax, confidence, class_id]
        if results and hasattr(results, 'xyxy') and len(results.xyxy) > 0:
            detections = results.xyxy[0] 

            for det in detections:  # det is a tensor
                box = det[:4].cpu().numpy() # xmin, ymin, xmax, ymax
                score = det[4].item()
                class_id = int(det[5].item())
                
                if score > self.confidence_threshold:
                    if 0 <= class_id < len(self.coco_names):
                        class_name = self.coco_names[class_id]
                    else:
                        class_name = "unknown"
                        print(f"Warning: Detected class_id {class_id} is out of bounds for coco_names.")
                        continue # Skip if class_id is invalid

                    # Check if this detected class is one of the targets and is enabled
                    if class_name in self.detection_targets and self.detection_targets[class_name]:
                        # Coordinates from YOLOv5 are already scaled to the original image size
                        # when a PIL image is passed directly.
                        x1, y1, x2, y2 = box.astype(int)
                        draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=3)
        
        data.add_optional_layer(detected_objects_layer_name, bbox_layer)

        return data