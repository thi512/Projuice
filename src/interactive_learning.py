"""
Interactive Learning Module
Allows users to annotate objects and train custom detectors
"""
import cv2
import numpy as np
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import json
import os
from collections import defaultdict
import pickle

logger = logging.getLogger(__name__)


class InteractiveLearningManager:
    """
    Manages interactive learning from user annotations
    Supports drawing boxes and text descriptions
    """

    def __init__(self, storage_dir="data/annotations"):
        """
        Initialize interactive learning manager

        Args:
            storage_dir: Directory to store annotations
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        os.makedirs(f"{storage_dir}/images", exist_ok=True)
        os.makedirs(f"{storage_dir}/labels", exist_ok=True)

        # Annotation storage
        self.annotations = []  # List of all annotations
        self.custom_classes = {}  # {class_name: class_id}
        self.pending_annotations = []  # Annotations not yet used for training

        # Learning statistics
        self.stats = {
            'total_annotations': 0,
            'classes_learned': 0,
            'training_sessions': 0,
            'accuracy_improvements': []
        }

        self.load_annotations()

    def add_annotation(self, frame: np.ndarray, bbox: Tuple[int, int, int, int],
                      class_name: str, description: str = "", confidence: float = 1.0):
        """
        Add a user annotation

        Args:
            frame: Image frame
            bbox: Bounding box (x1, y1, x2, y2)
            class_name: Object class name
            description: Text description
            confidence: User confidence (1.0 = certain)

        Returns:
            Annotation ID
        """
        annotation_id = f"anno_{len(self.annotations)}_{int(datetime.now().timestamp())}"

        # Save image crop
        x1, y1, x2, y2 = bbox
        crop = frame[y1:y2, x1:x2]
        image_path = f"{self.storage_dir}/images/{annotation_id}.jpg"
        cv2.imwrite(image_path, crop)

        # Create annotation record
        annotation = {
            'id': annotation_id,
            'timestamp': datetime.now().isoformat(),
            'class_name': class_name,
            'description': description,
            'bbox': bbox,
            'image_path': image_path,
            'confidence': confidence,
            'frame_shape': frame.shape,
            'verified': True,  # User-provided is trusted
            'used_for_training': False
        }

        self.annotations.append(annotation)
        self.pending_annotations.append(annotation)

        # Add to custom classes if new
        if class_name not in self.custom_classes:
            self.custom_classes[class_name] = len(self.custom_classes)
            self.stats['classes_learned'] += 1

        self.stats['total_annotations'] += 1

        # Save YOLO format label
        self._save_yolo_label(annotation, frame.shape)

        # Auto-save
        self.save_annotations()

        logger.info(f"Added annotation: {class_name} - '{description}'")

        return annotation_id

    def _save_yolo_label(self, annotation: Dict, frame_shape: Tuple):
        """
        Save annotation in YOLO format for training

        Args:
            annotation: Annotation dict
            frame_shape: Original frame shape (H, W, C)
        """
        height, width = frame_shape[:2]
        x1, y1, x2, y2 = annotation['bbox']

        # Convert to YOLO format (normalized center x, y, width, height)
        center_x = ((x1 + x2) / 2) / width
        center_y = ((y1 + y2) / 2) / height
        box_width = (x2 - x1) / width
        box_height = (y2 - y1) / height

        class_id = self.custom_classes[annotation['class_name']]

        label_path = annotation['image_path'].replace('/images/', '/labels/').replace('.jpg', '.txt')
        with open(label_path, 'w') as f:
            f.write(f"{class_id} {center_x} {center_y} {box_width} {box_height}\n")

    def add_correction(self, detection_id: str, correct_class: str,
                      correct_bbox: Tuple[int, int, int, int] = None):
        """
        Correct a detection made by the system

        Args:
            detection_id: ID of detection to correct
            correct_class: Correct class name
            correct_bbox: Corrected bounding box (optional)

        This teaches the system from its mistakes!
        """
        correction = {
            'id': f"correction_{int(datetime.now().timestamp())}",
            'timestamp': datetime.now().isoformat(),
            'detection_id': detection_id,
            'correct_class': correct_class,
            'correct_bbox': correct_bbox,
            'type': 'correction'
        }

        self.annotations.append(correction)
        self.pending_annotations.append(correction)
        self.save_annotations()

        logger.info(f"Added correction: {detection_id} → {correct_class}")

    def add_text_description(self, text_description: str, frame: np.ndarray,
                            bbox: Tuple[int, int, int, int] = None):
        """
        Add object with text description

        Examples:
        - "red car with white stripe"
        - "my dog Max"
        - "person wearing blue shirt"

        Args:
            text_description: Natural language description
            frame: Image frame
            bbox: Bounding box (if known)

        Returns:
            Annotation ID
        """
        # Parse description to extract class
        parsed = self._parse_description(text_description)

        class_name = parsed['class']
        attributes = parsed['attributes']

        annotation_id = self.add_annotation(
            frame=frame,
            bbox=bbox,
            class_name=class_name,
            description=text_description
        )

        # Store attributes for enhanced learning
        for anno in self.annotations:
            if anno['id'] == annotation_id:
                anno['attributes'] = attributes
                break

        logger.info(f"Added text-based annotation: '{text_description}' → {class_name}")

        return annotation_id

    def _parse_description(self, description: str) -> Dict:
        """
        Parse natural language description

        Args:
            description: Text description

        Returns:
            Dict with class and attributes
        """
        description_lower = description.lower()

        # Common object keywords
        object_keywords = {
            'car': 'vehicle',
            'truck': 'vehicle',
            'bus': 'vehicle',
            'motorcycle': 'vehicle',
            'bicycle': 'vehicle',
            'person': 'person',
            'people': 'person',
            'dog': 'pet',
            'cat': 'pet',
            'bird': 'bird',
            'package': 'package',
            'box': 'package'
        }

        # Find object type
        detected_class = 'object'
        for keyword, obj_class in object_keywords.items():
            if keyword in description_lower:
                detected_class = obj_class
                break

        # Extract attributes (colors, etc.)
        attributes = {
            'color': None,
            'size': None,
            'name': None
        }

        # Colors
        colors = ['red', 'blue', 'green', 'yellow', 'black', 'white', 'gray', 'silver', 'brown']
        for color in colors:
            if color in description_lower:
                attributes['color'] = color
                break

        # Sizes
        sizes = ['small', 'medium', 'large', 'tiny', 'huge', 'big']
        for size in sizes:
            if size in description_lower:
                attributes['size'] = size
                break

        return {
            'class': detected_class,
            'attributes': attributes,
            'raw_description': description
        }

    def get_pending_count(self) -> int:
        """Get number of annotations not yet used for training"""
        return len(self.pending_annotations)

    def get_class_distribution(self) -> Dict:
        """Get distribution of annotated classes"""
        distribution = defaultdict(int)
        for anno in self.annotations:
            if 'class_name' in anno:
                distribution[anno['class_name']] += 1
        return dict(distribution)

    def export_for_training(self, output_dir: str = "data/training_data"):
        """
        Export annotations in format ready for YOLO training

        Args:
            output_dir: Output directory

        Returns:
            Dict with training info
        """
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/images/train", exist_ok=True)
        os.makedirs(f"{output_dir}/labels/train", exist_ok=True)

        # Copy images and labels
        import shutil

        exported = 0
        for anno in self.pending_annotations:
            if 'image_path' in anno and os.path.exists(anno['image_path']):
                # Copy image
                shutil.copy(
                    anno['image_path'],
                    f"{output_dir}/images/train/{os.path.basename(anno['image_path'])}"
                )

                # Copy label
                label_path = anno['image_path'].replace('/images/', '/labels/').replace('.jpg', '.txt')
                if os.path.exists(label_path):
                    shutil.copy(
                        label_path,
                        f"{output_dir}/labels/train/{os.path.basename(label_path)}"
                    )

                exported += 1

        # Create data.yaml for YOLO training
        data_yaml = {
            'path': output_dir,
            'train': 'images/train',
            'val': 'images/train',  # Use same for validation initially
            'names': {v: k for k, v in self.custom_classes.items()}
        }

        with open(f"{output_dir}/data.yaml", 'w') as f:
            import yaml
            yaml.dump(data_yaml, f)

        logger.info(f"Exported {exported} annotations for training")

        return {
            'exported_count': exported,
            'classes': len(self.custom_classes),
            'output_dir': output_dir
        }

    def trigger_training(self, epochs: int = 10, batch_size: int = 16):
        """
        Trigger fine-tuning of YOLO model with user annotations

        Args:
            epochs: Number of training epochs
            batch_size: Batch size

        Returns:
            Training results
        """
        if self.get_pending_count() < 10:
            logger.warning(f"Need at least 10 annotations, have {self.get_pending_count()}")
            return {
                'success': False,
                'message': f'Need at least 10 annotations (have {self.get_pending_count()})'
            }

        # Export data
        export_info = self.export_for_training()

        # Train model (this is simplified - actual training takes time)
        try:
            from ultralytics import YOLO

            # Load base model
            model = YOLO('yolov8n.pt')

            # Fine-tune with user data
            results = model.train(
                data=f"{export_info['output_dir']}/data.yaml",
                epochs=epochs,
                batch=batch_size,
                imgsz=640,
                name='custom_training',
                patience=5,
                save=True,
                device='cuda' if self._check_cuda() else 'cpu'
            )

            # Mark annotations as used
            for anno in self.pending_annotations:
                anno['used_for_training'] = True
            self.pending_annotations = []

            self.stats['training_sessions'] += 1
            self.save_annotations()

            logger.info("Training completed successfully")

            return {
                'success': True,
                'message': 'Training completed',
                'epochs': epochs,
                'model_path': 'runs/detect/custom_training/weights/best.pt'
            }

        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {
                'success': False,
                'message': f'Training failed: {str(e)}'
            }

    def _check_cuda(self) -> bool:
        """Check if CUDA is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False

    def get_annotations_by_class(self, class_name: str) -> List[Dict]:
        """Get all annotations for a specific class"""
        return [a for a in self.annotations if a.get('class_name') == class_name]

    def get_recent_annotations(self, limit: int = 20) -> List[Dict]:
        """Get recent annotations"""
        return sorted(
            self.annotations,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )[:limit]

    def delete_annotation(self, annotation_id: str) -> bool:
        """Delete an annotation"""
        for i, anno in enumerate(self.annotations):
            if anno['id'] == annotation_id:
                # Delete files
                if 'image_path' in anno and os.path.exists(anno['image_path']):
                    os.remove(anno['image_path'])

                label_path = anno['image_path'].replace('/images/', '/labels/').replace('.jpg', '.txt')
                if os.path.exists(label_path):
                    os.remove(label_path)

                # Remove from lists
                self.annotations.pop(i)
                if anno in self.pending_annotations:
                    self.pending_annotations.remove(anno)

                self.save_annotations()
                logger.info(f"Deleted annotation: {annotation_id}")
                return True

        return False

    def get_statistics(self) -> Dict:
        """Get learning statistics"""
        return {
            **self.stats,
            'pending_annotations': self.get_pending_count(),
            'class_distribution': self.get_class_distribution(),
            'total_classes': len(self.custom_classes),
            'ready_for_training': self.get_pending_count() >= 10
        }

    def save_annotations(self):
        """Save all annotations to disk"""
        save_data = {
            'annotations': self.annotations,
            'custom_classes': self.custom_classes,
            'stats': self.stats
        }

        with open(f"{self.storage_dir}/annotations.json", 'w') as f:
            json.dump(save_data, f, indent=2, default=str)

    def load_annotations(self):
        """Load annotations from disk"""
        annotations_file = f"{self.storage_dir}/annotations.json"

        if os.path.exists(annotations_file):
            try:
                with open(annotations_file, 'r') as f:
                    data = json.load(f)

                self.annotations = data.get('annotations', [])
                self.custom_classes = data.get('custom_classes', {})
                self.stats = data.get('stats', self.stats)

                # Rebuild pending list
                self.pending_annotations = [
                    a for a in self.annotations
                    if not a.get('used_for_training', False)
                ]

                logger.info(f"Loaded {len(self.annotations)} annotations")
            except Exception as e:
                logger.error(f"Failed to load annotations: {e}")

    def suggest_annotations(self, detections: List[Dict]) -> List[Dict]:
        """
        Suggest which detections user should annotate

        Based on:
        - Low confidence detections
        - New/rare classes
        - Uncertain predictions

        Args:
            detections: List of current detections

        Returns:
            List of suggested annotations
        """
        suggestions = []

        for det in detections:
            # Low confidence - needs verification
            if det.get('confidence', 1.0) < 0.7:
                suggestions.append({
                    'detection': det,
                    'reason': 'Low confidence',
                    'priority': 'high'
                })

            # Check if class is under-represented
            class_name = det.get('class', '')
            class_count = self.get_class_distribution().get(class_name, 0)

            if class_count < 5:
                suggestions.append({
                    'detection': det,
                    'reason': f'Only {class_count} examples of {class_name}',
                    'priority': 'medium'
                })

        return suggestions[:5]  # Top 5 suggestions
