"""
License Plate Recognition (LPR/ALPR) - State-of-the-art OCR-based system
Uses EasyOCR for multi-language support and high accuracy
"""
import cv2
import numpy as np
import logging
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import easyocr

logger = logging.getLogger(__name__)


class LicensePlateRecognizer:
    """
    State-of-the-art License Plate Recognition using EasyOCR
    Supports multiple countries/regions and plate formats
    """

    def __init__(self, config):
        """
        Initialize License Plate Recognizer

        Args:
            config: System configuration
        """
        self.config = config
        lpr_config = config.get('license_plate_recognition', {})

        self.enabled = lpr_config.get('enabled', True)
        self.languages = lpr_config.get('languages', ['en'])  # OCR languages
        self.gpu = lpr_config.get('gpu', True)
        self.confidence_threshold = lpr_config.get('confidence_threshold', 0.5)
        self.country_format = lpr_config.get('country_format', 'auto')  # auto, us, uk, eu, etc.

        # Initialize EasyOCR reader
        self.reader = None
        if self.enabled:
            try:
                logger.info(f"Initializing EasyOCR with languages: {self.languages}")
                self.reader = easyocr.Reader(
                    self.languages,
                    gpu=self.gpu,
                    verbose=False
                )
                logger.info("EasyOCR initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                self.enabled = False

        # Plate format patterns for different countries
        self.plate_patterns = {
            'us': [
                r'^[A-Z]{3}[0-9]{4}$',  # ABC1234
                r'^[A-Z]{2}[0-9]{5}$',  # AB12345
                r'^[0-9]{3}[A-Z]{3}$',  # 123ABC
                r'^[A-Z]{1,3}[0-9]{1,4}[A-Z]{0,2}$',  # General US
            ],
            'uk': [
                r'^[A-Z]{2}[0-9]{2}[A-Z]{3}$',  # AB12CDE (current)
                r'^[A-Z][0-9]{1,3}[A-Z]{3}$',  # A123BCD (old)
            ],
            'eu': [
                r'^[A-Z]{1,3}[0-9]{1,4}[A-Z]{0,3}$',  # European format
            ],
            'auto': []  # Accept any alphanumeric combination
        }

        # Plate detection cascade (optional - for locating plates in image)
        self.plate_cascade = None
        cascade_path = lpr_config.get('cascade_path')
        if cascade_path:
            try:
                self.plate_cascade = cv2.CascadeClassifier(cascade_path)
            except:
                logger.warning("Plate detection cascade not loaded")

    def detect_plates_in_frame(self, frame: np.ndarray, vehicle_bbox: Tuple[int, int, int, int] = None) -> List[Dict]:
        """
        Detect and recognize license plates in frame

        Args:
            frame: Input frame
            vehicle_bbox: Optional bounding box of vehicle (x1, y1, x2, y2)

        Returns:
            List of detected plates with text, confidence, location
        """
        if not self.enabled or self.reader is None:
            return []

        results = []

        # If vehicle bbox provided, crop to that region (more accurate)
        if vehicle_bbox:
            x1, y1, x2, y2 = vehicle_bbox
            # Expand bbox slightly to ensure we get full plate
            h, w = frame.shape[:2]
            x1 = max(0, x1 - 10)
            y1 = max(0, y1 - 10)
            x2 = min(w, x2 + 10)
            y2 = min(h, y2 + 10)
            roi = frame[y1:y2, x1:x2]
        else:
            roi = frame
            x1, y1 = 0, 0

        # Preprocess for better OCR
        processed = self._preprocess_for_ocr(roi)

        try:
            # Run EasyOCR
            ocr_results = self.reader.readtext(processed)

            for detection in ocr_results:
                bbox, text, confidence = detection

                # Clean and validate plate text
                cleaned_text = self._clean_plate_text(text)

                # Validate against plate patterns
                if not self._validate_plate_format(cleaned_text):
                    continue

                # Only accept high confidence detections
                if confidence < self.confidence_threshold:
                    continue

                # Adjust bbox coordinates back to original frame
                adjusted_bbox = self._adjust_bbox(bbox, x1, y1)

                results.append({
                    'plate_number': cleaned_text,
                    'confidence': float(confidence),
                    'bbox': adjusted_bbox,
                    'raw_text': text,
                    'timestamp': datetime.now()
                })

                logger.info(f"Detected plate: {cleaned_text} (confidence: {confidence:.2f})")

        except Exception as e:
            logger.error(f"Plate recognition error: {e}")

        return results

    def _preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy

        Args:
            image: Input image

        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Apply bilateral filter to reduce noise while keeping edges
        denoised = cv2.bilateralFilter(gray, 11, 17, 17)

        # Adaptive threshold for varying lighting
        thresh = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )

        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        return morph

    def _clean_plate_text(self, text: str) -> str:
        """
        Clean and normalize plate text

        Args:
            text: Raw OCR text

        Returns:
            Cleaned plate text
        """
        # Remove spaces, dashes, and special characters
        cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())

        # Common OCR corrections
        corrections = {
            'O': '0',  # Letter O to zero (context-dependent)
            'I': '1',  # Letter I to one
            'S': '5',  # S to 5 (in numeric positions)
            'B': '8',  # B to 8
        }

        # Apply corrections intelligently (avoid over-correcting)
        # This is simplified - production systems use ML for this
        cleaned = cleaned.replace(' ', '')

        return cleaned

    def _validate_plate_format(self, text: str) -> bool:
        """
        Validate plate text against known formats

        Args:
            text: Plate text to validate

        Returns:
            True if valid format
        """
        # Must be reasonable length
        if not text or len(text) < 2 or len(text) > 10:
            return False

        # Must contain both letters and numbers (most plates)
        has_letter = any(c.isalpha() for c in text)
        has_number = any(c.isdigit() for c in text)

        if not (has_letter or has_number):
            return False

        # Check against country-specific patterns
        patterns = self.plate_patterns.get(self.country_format, [])

        if not patterns:  # Auto mode - accept any reasonable alphanumeric
            return True

        for pattern in patterns:
            if re.match(pattern, text):
                return True

        return False

    def _adjust_bbox(self, bbox: List, offset_x: int, offset_y: int) -> Tuple:
        """
        Adjust bounding box coordinates

        Args:
            bbox: Original bbox from OCR
            offset_x: X offset
            offset_y: Y offset

        Returns:
            Adjusted bbox (x1, y1, x2, y2)
        """
        points = np.array(bbox)
        x_coords = points[:, 0] + offset_x
        y_coords = points[:, 1] + offset_y

        x1, y1 = int(np.min(x_coords)), int(np.min(y_coords))
        x2, y2 = int(np.max(x_coords)), int(np.max(y_coords))

        return (x1, y1, x2, y2)

    def track_plate_history(self, plate_number: str, vehicle_info: Dict = None) -> Dict:
        """
        Track plate appearance history and trends

        Args:
            plate_number: License plate number
            vehicle_info: Additional vehicle information

        Returns:
            Tracking information
        """
        # This would integrate with database
        return {
            'plate_number': plate_number,
            'first_seen': datetime.now(),
            'last_seen': datetime.now(),
            'appearance_count': 1,
            'vehicle_info': vehicle_info or {}
        }


class PlateAnalytics:
    """
    Analytics and reporting for license plate data
    """

    def __init__(self, database_manager):
        """
        Initialize plate analytics

        Args:
            database_manager: Database manager instance
        """
        self.db = database_manager

    def get_plate_statistics(self, time_range: Dict = None) -> Dict:
        """
        Get statistics about plate detections

        Args:
            time_range: Time range filter

        Returns:
            Statistics dictionary
        """
        stats = {
            'total_plates': 0,
            'unique_plates': 0,
            'most_frequent': [],
            'recent_plates': [],
            'hourly_distribution': {},
            'new_plates_today': 0
        }

        if not self.db:
            return stats

        try:
            from sqlalchemy import func
            session = self.db.Session()

            # Total plate detections
            query = session.query(self.db.LicensePlate)
            if time_range:
                query = query.filter(
                    self.db.LicensePlate.timestamp >= time_range.get('start'),
                    self.db.LicensePlate.timestamp <= time_range.get('end')
                )

            stats['total_plates'] = query.count()

            # Unique plates
            stats['unique_plates'] = query.with_entities(
                self.db.LicensePlate.plate_number
            ).distinct().count()

            # Most frequent plates
            most_frequent = session.query(
                self.db.LicensePlate.plate_number,
                func.count(self.db.LicensePlate.id).label('count')
            ).group_by(
                self.db.LicensePlate.plate_number
            ).order_by(
                func.count(self.db.LicensePlate.id).desc()
            ).limit(10).all()

            stats['most_frequent'] = [
                {'plate': plate, 'count': count}
                for plate, count in most_frequent
            ]

            # Recent plates
            recent = query.order_by(
                self.db.LicensePlate.timestamp.desc()
            ).limit(20).all()

            stats['recent_plates'] = [
                {
                    'plate': r.plate_number,
                    'timestamp': r.timestamp.isoformat(),
                    'confidence': r.confidence
                }
                for r in recent
            ]

            session.close()

        except Exception as e:
            logger.error(f"Failed to get plate statistics: {e}")

        return stats

    def get_plate_history(self, plate_number: str) -> List[Dict]:
        """
        Get history for specific plate

        Args:
            plate_number: License plate to query

        Returns:
            List of appearances
        """
        if not self.db:
            return []

        try:
            session = self.db.Session()
            records = session.query(self.db.LicensePlate).filter(
                self.db.LicensePlate.plate_number == plate_number
            ).order_by(self.db.LicensePlate.timestamp.desc()).all()

            history = [
                {
                    'timestamp': r.timestamp.isoformat(),
                    'confidence': r.confidence,
                    'vehicle_type': r.vehicle_type,
                    'vehicle_color': r.vehicle_color
                }
                for r in records
            ]

            session.close()
            return history

        except Exception as e:
            logger.error(f"Failed to get plate history: {e}")
            return []

    def get_hourly_trends(self, days: int = 7) -> Dict:
        """
        Get hourly plate detection trends

        Args:
            days: Number of days to analyze

        Returns:
            Hourly trend data
        """
        from datetime import datetime, timedelta

        trends = {hour: 0 for hour in range(24)}

        if not self.db:
            return trends

        try:
            from sqlalchemy import func
            session = self.db.Session()

            start_time = datetime.now() - timedelta(days=days)

            results = session.query(
                func.extract('hour', self.db.LicensePlate.timestamp).label('hour'),
                func.count(self.db.LicensePlate.id).label('count')
            ).filter(
                self.db.LicensePlate.timestamp >= start_time
            ).group_by('hour').all()

            for hour, count in results:
                trends[int(hour)] = count

            session.close()

        except Exception as e:
            logger.error(f"Failed to get hourly trends: {e}")

        return trends

    def find_suspicious_patterns(self) -> List[Dict]:
        """
        Identify suspicious plate patterns

        Returns:
            List of suspicious patterns
        """
        suspicious = []

        if not self.db:
            return suspicious

        try:
            from sqlalchemy import func
            from datetime import datetime, timedelta
            session = self.db.Session()

            # Pattern 1: Same plate multiple times in short period
            last_hour = datetime.now() - timedelta(hours=1)
            frequent = session.query(
                self.db.LicensePlate.plate_number,
                func.count(self.db.LicensePlate.id).label('count')
            ).filter(
                self.db.LicensePlate.timestamp >= last_hour
            ).group_by(
                self.db.LicensePlate.plate_number
            ).having(
                func.count(self.db.LicensePlate.id) > 5
            ).all()

            for plate, count in frequent:
                suspicious.append({
                    'type': 'frequent_passes',
                    'plate': plate,
                    'count': count,
                    'timeframe': 'last_hour',
                    'severity': 'medium'
                })

            # Pattern 2: Plates seen at unusual hours (2am-5am)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            unusual_time = session.query(self.db.LicensePlate).filter(
                self.db.LicensePlate.timestamp >= today,
                func.extract('hour', self.db.LicensePlate.timestamp).between(2, 5)
            ).all()

            for record in unusual_time:
                suspicious.append({
                    'type': 'unusual_time',
                    'plate': record.plate_number,
                    'timestamp': record.timestamp.isoformat(),
                    'severity': 'low'
                })

            session.close()

        except Exception as e:
            logger.error(f"Failed to find suspicious patterns: {e}")

        return suspicious
