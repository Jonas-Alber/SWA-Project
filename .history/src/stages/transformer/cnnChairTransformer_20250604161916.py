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
        self.target_object_names = ["chair", "person", "car", "dog", "cat", "tvmonitor"] # tvmonitor is often 'tv' in COCO
        
        # Ensure 'tvmonitor' or 'tv' is in coco_names, adjust if necessary
        # This logic might need adjustment based on exact names in YOLOv5's COCO list
        if self.coco_names and 'tvmonitor' not in self.coco_names and 'tv' in self.coco_names:
            try:
                idx = self.target_object_names.index('tvmonitor')
                self.target_object_names[idx] = 'tv'
            except ValueError:
                pass # 'tvmonitor' was not in the initial list

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
        Detect configured objects using a CNN and add their bounding boxes as an optional layer.
        """
        detected_objects_layer_name = f"{self.__class__.__name__}_detected_objects_bboxes"
        data.remove_optional_layer(detected_objects_layer_name)

        if not self._stage_visible:
            return data
        
        # --- CNN Object Detection ---
        if not isinstance(data.base_image, Image.Image):
            print("Warning: base_image is not a PIL Image. Skipping object detection.")
            return data

        pil_image = data.base_image.convert("RGB")
        
        preprocess = FasterRCNN_ResNet50_FPN_Weights.DEFAULT.transforms()
        img_tensor_batch = preprocess(pil_image)
        
        if img_tensor_batch.ndim == 3:
            img_tensor_list = [img_tensor_batch]
        else:
            img_tensor_list = [img_tensor_batch[i] for i in range(img_tensor_batch.shape[0])]

        with torch.no_grad():
            prediction = self.detection_model(img_tensor_list)
        
        bbox_layer = Image.new("RGBA", data.base_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(bbox_layer)
        
        if prediction and len(prediction) > 0:
            pred_labels = prediction[0]['labels']
            pred_scores = prediction[0]['scores']
            pred_boxes = prediction[0]['boxes']

            for i in range(len(pred_labels)):
                score = pred_scores[i].item()
                
                if score > self.confidence_threshold:
                    label_id = pred_labels[i].item()
                    class_name = "unknown"
                    
                    # Try to map label_id to class name (model output is typically 1-indexed for COCO)
                    if 0 <= (label_id - 1) < len(self.coco_names):
                        class_name = self.coco_names[label_id - 1]
                    # Fallback for 0-indexed (less common for this model with COCO)
                    elif 0 <= label_id < len(self.coco_names) and class_name == "unknown": 
                         class_name = self.coco_names[label_id]

                    # Check if this detected class is one of the targets and is enabled
                    if class_name in self.detection_targets and self.detection_targets[class_name]:
                        # Scale boxes from the transformed tensor size back to the original image size
                        box = pred_boxes[i].cpu().numpy()
                        proc_h, proc_w = img_tensor_batch.shape[1], img_tensor_batch.shape[2]
                        orig_w, orig_h = data.base_image.size
                        scale_x = orig_w / proc_w
                        scale_y = orig_h / proc_h
                        # apply scaling and convert to int coordinates
                        x1, y1, x2, y2 = (box * np.array([scale_x, scale_y, scale_x, scale_y])).astype(int)
                        draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=3)
        
        data.add_optional_layer(detected_objects_layer_name, bbox_layer)

        return data