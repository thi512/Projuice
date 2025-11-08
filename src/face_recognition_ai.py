"""
Advanced face recognition with learning and person tracking
"""
import face_recognition
import cv2
import numpy as np
import logging
import pickle
import os
from datetime import datetime
from typing import List, Dict, Tuple
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class FaceRecognitionSystem:
    """Advanced face recognition with learning capabilities"""

    def __init__(self, tolerance=0.6, storage_dir="data/faces"):
        """
        Initialize face recognition system

        Args:
            tolerance: Face matching tolerance (lower = stricter)
            storage_dir: Directory to store face encodings
        """
        self.tolerance = tolerance
        self.storage_dir = storage_dir
        self.known_faces = {}  # {person_id: {'encodings': [], 'name': '', 'first_seen': '', 'last_seen': ''}}
        self.unknown_faces = []  # Temporary storage for unknown faces
        self.face_locations = []
        self.face_encodings = []

        os.makedirs(storage_dir, exist_ok=True)
        self.load_known_faces()

    def load_known_faces(self):
        """Load known faces from storage"""
        faces_file = os.path.join(self.storage_dir, "known_faces.pkl")
        if os.path.exists(faces_file):
            try:
                with open(faces_file, 'rb') as f:
                    self.known_faces = pickle.load(f)
                logger.info(f"Loaded {len(self.known_faces)} known faces")
            except Exception as e:
                logger.error(f"Failed to load known faces: {e}")
                self.known_faces = {}

    def save_known_faces(self):
        """Save known faces to storage"""
        faces_file = os.path.join(self.storage_dir, "known_faces.pkl")
        try:
            with open(faces_file, 'wb') as f:
                pickle.dump(self.known_faces, f)
            logger.info(f"Saved {len(self.known_faces)} known faces")
        except Exception as e:
            logger.error(f"Failed to save known faces: {e}")

    def detect_and_recognize(self, frame):
        """
        Detect and recognize faces in frame

        Args:
            frame: Input image frame

        Returns:
            List of face detections with recognition info
        """
        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Find all faces and encodings
        self.face_locations = face_recognition.face_locations(rgb_small_frame)
        self.face_encodings = face_recognition.face_encodings(rgb_small_frame, self.face_locations)

        results = []

        for face_encoding, face_location in zip(self.face_encodings, self.face_locations):
            # Scale back up face locations
            top, right, bottom, left = face_location
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Try to match with known faces
            person_id, confidence = self._match_face(face_encoding)

            if person_id:
                # Update last seen
                self.known_faces[person_id]['last_seen'] = datetime.now().isoformat()
                name = self.known_faces[person_id]['name']
            else:
                # Unknown face - assign temporary ID
                person_id = f"unknown_{len(self.unknown_faces)}"
                name = "Unknown"
                confidence = 0.0

                # Store for potential learning
                self.unknown_faces.append({
                    'encoding': face_encoding,
                    'first_seen': datetime.now().isoformat(),
                    'count': 1
                })

            results.append({
                'person_id': person_id,
                'name': name,
                'confidence': confidence,
                'location': (left, top, right, bottom),
                'encoding': face_encoding
            })

        return results

    def _match_face(self, face_encoding):
        """
        Match face encoding with known faces

        Returns:
            Tuple of (person_id, confidence) or (None, 0.0)
        """
        if not self.known_faces:
            return None, 0.0

        # Compare with all known faces
        for person_id, person_data in self.known_faces.items():
            known_encodings = person_data['encodings']

            # Calculate distances
            distances = face_recognition.face_distance(known_encodings, face_encoding)

            if len(distances) > 0:
                min_distance = np.min(distances)

                if min_distance < self.tolerance:
                    confidence = 1.0 - min_distance
                    return person_id, confidence

        return None, 0.0

    def learn_face(self, face_encoding, person_id=None, name=None):
        """
        Learn a new face or add to existing person

        Args:
            face_encoding: Face encoding to learn
            person_id: Person ID (auto-generated if None)
            name: Person name (default: "Person N")
        """
        if person_id is None:
            person_id = f"person_{len(self.known_faces) + 1}"

        if person_id in self.known_faces:
            # Add encoding to existing person
            self.known_faces[person_id]['encodings'].append(face_encoding)
            logger.info(f"Added new encoding for {name or person_id}")
        else:
            # Create new person
            if name is None:
                name = f"Person {len(self.known_faces) + 1}"

            self.known_faces[person_id] = {
                'encodings': [face_encoding],
                'name': name,
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'appearances': 1
            }
            logger.info(f"Learned new face: {name} ({person_id})")

        self.save_known_faces()

    def auto_learn_frequent_unknowns(self, min_appearances=5):
        """
        Automatically learn faces that appear frequently

        Args:
            min_appearances: Minimum number of appearances to auto-learn
        """
        # Group similar unknown faces
        face_groups = []

        for unknown in self.unknown_faces:
            matched = False

            for group in face_groups:
                distances = face_recognition.face_distance(
                    [f['encoding'] for f in group],
                    unknown['encoding']
                )

                if np.min(distances) < self.tolerance:
                    group.append(unknown)
                    matched = True
                    break

            if not matched:
                face_groups.append([unknown])

        # Learn groups that appear frequently
        learned = 0
        for group in face_groups:
            if len(group) >= min_appearances:
                # Calculate average encoding
                avg_encoding = np.mean([f['encoding'] for f in group], axis=0)

                # Learn this face
                self.learn_face(
                    avg_encoding,
                    name=f"Frequent Visitor {len(self.known_faces) + 1}"
                )
                learned += 1

        if learned > 0:
            self.unknown_faces = []  # Clear learned unknowns
            logger.info(f"Auto-learned {learned} frequently appearing faces")

    def get_known_people(self):
        """Get list of all known people"""
        return [
            {
                'person_id': pid,
                'name': data['name'],
                'first_seen': data['first_seen'],
                'last_seen': data['last_seen'],
                'num_encodings': len(data['encodings'])
            }
            for pid, data in self.known_faces.items()
        ]

    def rename_person(self, person_id, new_name):
        """Rename a person"""
        if person_id in self.known_faces:
            self.known_faces[person_id]['name'] = new_name
            self.save_known_faces()
            logger.info(f"Renamed {person_id} to {new_name}")
            return True
        return False

    def delete_person(self, person_id):
        """Delete a person from known faces"""
        if person_id in self.known_faces:
            del self.known_faces[person_id]
            self.save_known_faces()
            logger.info(f"Deleted person {person_id}")
            return True
        return False

    def draw_faces(self, frame, detections):
        """
        Draw face boxes and labels on frame

        Args:
            frame: Input frame
            detections: List of face detections

        Returns:
            Frame with drawn faces
        """
        output = frame.copy()

        for detection in detections:
            left, top, right, bottom = detection['location']
            name = detection['name']
            confidence = detection['confidence']

            # Choose color based on recognition
            color = (0, 255, 0) if name != "Unknown" else (0, 165, 255)

            # Draw box
            cv2.rectangle(output, (left, top), (right, bottom), color, 2)

            # Draw label
            label = f"{name} ({confidence:.2f})" if confidence > 0 else name
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)

            cv2.rectangle(output, (left, top - 30), (left + label_size[0], top), color, -1)
            cv2.putText(output, label, (left, top - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return output

    def export_statistics(self):
        """Export face recognition statistics"""
        return {
            'total_known_people': len(self.known_faces),
            'total_unknown_faces': len(self.unknown_faces),
            'known_people': self.get_known_people()
        }
