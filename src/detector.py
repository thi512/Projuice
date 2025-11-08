"""
ML-based object detection module using YOLO
"""
import cv2
import numpy as np
import logging
from typing import List, Tuple, Dict
import os

logger = logging.getLogger(__name__)


class ObjectDetector:
    """Object detection using YOLO models"""

    def __init__(self, model_type="yolov8n", confidence_threshold=0.5, device="cpu"):
        """
        Initialize object detector

        Args:
            model_type: YOLO model variant (yolov8n, yolov8s, yolov8m, yolov8l, yolov8x)
            confidence_threshold: Minimum confidence for detections
            device: Device to run inference on (cpu, cuda, mps)
        """
        self.model_type = model_type
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.model = None

        try:
            from ultralytics import YOLO
            logger.info(f"Loading YOLO model: {model_type}")
            self.model = YOLO(f"{model_type}.pt")
            logger.info(f"Model loaded successfully on {device}")
        except ImportError:
            logger.error("ultralytics package not found. Install with: pip install ultralytics")
            raise
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise

    def detect(self, frame, target_classes=None):
        """
        Detect objects in frame

        Args:
            frame: Input image frame
            target_classes: List of class names to detect (None for all classes)

        Returns:
            List of detections with format: [(class_name, confidence, bbox), ...]
        """
        if self.model is None:
            return []

        # Run inference
        results = self.model(frame, conf=self.confidence_threshold, device=self.device, verbose=False)

        detections = []
        for result in results:
            boxes = result.boxes

            for box in boxes:
                # Extract box information
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                bbox = box.xyxy[0].cpu().numpy()  # x1, y1, x2, y2

                # Get class name
                class_name = result.names[cls_id]

                # Filter by target classes if specified
                if target_classes and class_name not in target_classes:
                    continue

                detections.append({
                    'class': class_name,
                    'confidence': conf,
                    'bbox': bbox.tolist(),
                    'class_id': cls_id
                })

        return detections

    def draw_detections(self, frame, detections):
        """
        Draw bounding boxes and labels on frame

        Args:
            frame: Input image frame
            detections: List of detections from detect()

        Returns:
            Frame with drawn detections
        """
        output = frame.copy()

        for det in detections:
            bbox = det['bbox']
            x1, y1, x2, y2 = map(int, bbox)
            class_name = det['class']
            confidence = det['confidence']

            # Draw bounding box
            color = self._get_class_color(det['class_id'])
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)

            # Draw label
            label = f"{class_name} {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            label_w, label_h = label_size

            # Draw label background
            cv2.rectangle(output, (x1, y1 - label_h - 10), (x1 + label_w, y1), color, -1)

            # Draw label text
            cv2.putText(output, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX,
                       0.5, (255, 255, 255), 2)

        return output

    def _get_class_color(self, class_id):
        """Get consistent color for each class"""
        np.random.seed(class_id)
        return tuple(map(int, np.random.randint(0, 255, 3)))


class MotionDetector:
    """Motion detection using background subtraction"""

    def __init__(self, threshold=25, min_area=500):
        """
        Initialize motion detector

        Args:
            threshold: Threshold for background subtraction
            min_area: Minimum contour area to consider as motion
        """
        self.threshold = threshold
        self.min_area = min_area
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=threshold,
            detectShadows=True
        )
        self.first_frame = None

    def detect(self, frame):
        """
        Detect motion in frame

        Args:
            frame: Input image frame

        Returns:
            tuple: (motion_detected, motion_mask, contours)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(gray)

        # Threshold
        _, thresh = cv2.threshold(fg_mask, self.threshold, 255, cv2.THRESH_BINARY)

        # Dilate to fill gaps
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter by area
        motion_contours = [c for c in contours if cv2.contourArea(c) > self.min_area]

        motion_detected = len(motion_contours) > 0

        return motion_detected, thresh, motion_contours

    def draw_motion(self, frame, contours):
        """
        Draw motion detection results

        Args:
            frame: Input image frame
            contours: Motion contours from detect()

        Returns:
            Frame with drawn motion areas
        """
        output = frame.copy()

        for contour in contours:
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)

        return output


class FaceDetector:
    """Face detection using Haar Cascades"""

    def __init__(self):
        """Initialize face detector"""
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    def detect(self, frame):
        """
        Detect faces in frame

        Args:
            frame: Input image frame

        Returns:
            List of face bounding boxes
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        return faces

    def draw_faces(self, frame, faces):
        """
        Draw face detection results

        Args:
            frame: Input image frame
            faces: Face bounding boxes from detect()

        Returns:
            Frame with drawn face boxes
        """
        output = frame.copy()

        for (x, y, w, h) in faces:
            cv2.rectangle(output, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(output, "Face", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                       0.5, (255, 0, 0), 2)

        return output
