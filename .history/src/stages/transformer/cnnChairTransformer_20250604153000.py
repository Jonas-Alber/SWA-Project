// ...existing code...
from PIL import Image, ImageDraw
import numpy as np
import cv2
from ...pipeline import StageConfigElement, PipeDataClass
from cv2 import aruco
import torch
import torchvision
from torchvision.models.detection import FasterRCNN_ResNet50_FPN_Weights

class CnnChairTransformer(AbcImageTransformer):
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
        # Load a pre-trained Faster R-CNN model
        self.detection_model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights=FasterRCNN_ResNet50_FPN_Weights.DEFAULT)
        self.detection_model.eval() # Set the model to evaluation mode
        # Get COCO class names
        self.coco_names = FasterRCNN_ResNet50_FPN_Weights.COCO_V1.meta['categories']
        # Find the index for 'chair'
        try:
            self.chair_label_index = self.coco_names.index('chair')
        except ValueError:
            print("Warning: 'chair' class not found in COCO names. Chair detection will not work.")
            self.chair_label_index = -1 # Invalid index

    def _loadDisplayImage(self, image: str):
// ...existing code...
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
        # Call super().setConfigElements only if it's defined in AbcImageTransformer and does something.
        # If AbcImageTransformer.setConfigElements is just a pass or abstract, this might not be needed
        # or should be adapted based on its actual implementation.
        # Assuming it handles general stage configurations like visibility:
        super().setConfigElements(config_elements)
    
    def process(self, data: PipeDataClass) -> PipeDataClass:
        """
        Detect an ArUco marker in data.base_image and warp the poster onto it.
        Also, detect chairs using a CNN and add their bounding boxes as another optional layer.
        """
        # Handle poster layer
        poster_layer_name = self.__class__.__name__
        data.remove_optional_layer(poster_layer_name)

        # Handle chair detection layer
        chair_bbox_layer_name = f"{self.__class__.__name__}_chair_bboxes"
        data.remove_optional_layer(chair_bbox_layer_name)

        if not self._stage_visible:
            return data

        # --- ArUco Poster Warping (existing code) ---
        frame_cv = cv2.cvtColor(np.array(data.base_image), cv2.COLOR_RGBA2BGRA) # Use base_image for ArUco
        poster_np = cv2.cvtColor(np.array(self._poster_image), cv2.COLOR_RGBA2BGRA)

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

        if frame_cv.shape[2] == 3:
            frame_cv = cv2.cvtColor(frame_cv, cv2.COLOR_BGR2BGRA)
        if poster_np.shape[2] == 3:
            poster_np = cv2.cvtColor(poster_np, cv2.COLOR_BGR2BGRA)

        aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_100)
        params = aruco.DetectorParameters()
        detector = aruco.ArucoDetector(aruco_dict, params)
        corners, ids, _ = detector.detectMarkers(frame_cv)

        if ids is not None and len(corners) > 0:
            dst = corners[0][0].astype(np.float32)
            M = cv2.getPerspectiveTransform(scaled_corners, dst)
            warped_poster_cv = cv2.warpPerspective(poster_np, M, (frame_cv.shape[1], frame_cv.shape[0]))
            warped_poster_pil = Image.fromarray(cv2.cvtColor(warped_poster_cv, cv2.COLOR_BGRA2RGBA))
            data.add_optional_layer(poster_layer_name, warped_poster_pil)
        
        # --- CNN Chair Detection ---
        if self.chair_label_index != -1:
            pil_image = data.base_image.convert("RGB") # Ensure image is RGB for the model
            
            # Preprocess the image
            transform = torchvision.transforms.Compose([torchvision.transforms.ToTensor()])
            img_tensor = transform(pil_image)
            
            # Perform detection
            with torch.no_grad():
                prediction = self.detection_model([img_tensor])
            
            # Create a transparent layer for bounding boxes
            bbox_layer = Image.new("RGBA", data.base_image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(bbox_layer)
            
            # Process detections
            for i in range(len(prediction[0]['labels'])):
                label_idx = prediction[0]['labels'][i].item()
                score = prediction[0]['scores'][i].item()
                
                # Check if the detected object is a chair and score is above a threshold
                if label_idx == self.chair_label_index and score > 0.5: # Confidence threshold 0.5
                    box = prediction[0]['boxes'][i].cpu().numpy()
                    x1, y1, x2, y2 = box
                    draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=3)
            
            data.add_optional_layer(chair_bbox_layer_name, bbox_layer)

        return data