"""
Behavioral analysis and pattern learning engine
"""
import numpy as np
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Tuple
import json
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle

logger = logging.getLogger(__name__)


class BehavioralAnalysisEngine:
    """Learn normal patterns and detect anomalies"""

    def __init__(self, storage_dir="data/behavior"):
        """
        Initialize behavioral analysis engine

        Args:
            storage_dir: Directory to store learned patterns
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

        # Pattern storage
        self.time_patterns = defaultdict(list)  # Patterns by hour of day
        self.daily_patterns = defaultdict(list)  # Patterns by day of week
        self.location_patterns = defaultdict(list)  # Patterns by location
        self.activity_patterns = defaultdict(int)  # Activity frequency

        # Person tracking
        self.person_behaviors = defaultdict(lambda: {
            'usual_times': defaultdict(int),
            'usual_paths': [],
            'dwell_times': [],
            'first_seen': None,
            'last_seen': None,
            'total_appearances': 0
        })

        # Anomaly detection
        self.anomaly_detector = None
        self.scaler = StandardScaler()
        self.anomaly_history = deque(maxlen=1000)

        # Learning data
        self.events_buffer = deque(maxlen=10000)

        self.load_patterns()

    def record_event(self, event_type: str, data: Dict):
        """
        Record an event for pattern learning

        Args:
            event_type: Type of event (person_detected, vehicle_passed, etc.)
            data: Event data dictionary
        """
        timestamp = datetime.now()

        event = {
            'type': event_type,
            'timestamp': timestamp.isoformat(),
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'data': data
        }

        self.events_buffer.append(event)

        # Update patterns
        self._update_patterns(event)

        # Check for anomalies
        if len(self.events_buffer) > 100:
            self._check_anomaly(event)

    def _update_patterns(self, event):
        """Update learned patterns based on event"""
        hour = event['hour']
        day = event['day_of_week']
        event_type = event['type']

        # Time-based patterns
        self.time_patterns[hour].append(event_type)
        self.daily_patterns[day].append(event_type)

        # Activity frequency
        self.activity_patterns[event_type] += 1

        # Person-specific patterns
        if event_type == 'person_detected' and 'person_id' in event['data']:
            person_id = event['data']['person_id']
            self._update_person_behavior(person_id, event)

    def _update_person_behavior(self, person_id: str, event: Dict):
        """Update behavior patterns for a specific person"""
        behavior = self.person_behaviors[person_id]
        timestamp = datetime.fromisoformat(event['timestamp'])

        # Update time patterns
        hour = event['hour']
        behavior['usual_times'][hour] += 1

        # Update appearance tracking
        if behavior['first_seen'] is None:
            behavior['first_seen'] = timestamp.isoformat()

        behavior['last_seen'] = timestamp.isoformat()
        behavior['total_appearances'] += 1

        # Track location if available
        if 'location' in event['data']:
            behavior['usual_paths'].append(event['data']['location'])

    def learn_normal_behavior(self):
        """
        Learn what constitutes normal behavior from historical data

        This trains an anomaly detection model
        """
        if len(self.events_buffer) < 100:
            logger.warning("Not enough data to learn patterns (need at least 100 events)")
            return False

        # Extract features from events
        features = []

        for event in self.events_buffer:
            feature_vector = self._extract_features(event)
            features.append(feature_vector)

        features = np.array(features)

        # Normalize features
        features_scaled = self.scaler.fit_transform(features)

        # Train anomaly detector
        self.anomaly_detector = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42
        )
        self.anomaly_detector.fit(features_scaled)

        logger.info(f"Learned normal behavior from {len(self.events_buffer)} events")
        self.save_patterns()

        return True

    def _extract_features(self, event) -> np.ndarray:
        """
        Extract numerical features from event for ML

        Returns:
            Feature vector
        """
        features = [
            event['hour'],  # Hour of day
            event['day_of_week'],  # Day of week
            hash(event['type']) % 1000,  # Event type (hashed)
        ]

        # Add event-specific features
        if 'count' in event['data']:
            features.append(event['data']['count'])
        else:
            features.append(0)

        if 'confidence' in event['data']:
            features.append(event['data']['confidence'])
        else:
            features.append(0)

        return np.array(features)

    def _check_anomaly(self, event) -> bool:
        """
        Check if event is anomalous

        Returns:
            True if anomaly detected
        """
        if self.anomaly_detector is None:
            return False

        features = self._extract_features(event).reshape(1, -1)
        features_scaled = self.scaler.transform(features)

        prediction = self.anomaly_detector.predict(features_scaled)[0]
        score = self.anomaly_detector.score_samples(features_scaled)[0]

        is_anomaly = prediction == -1

        if is_anomaly:
            anomaly_record = {
                'timestamp': event['timestamp'],
                'type': event['type'],
                'score': float(score),
                'data': event['data']
            }
            self.anomaly_history.append(anomaly_record)

            logger.warning(f"Anomaly detected: {event['type']} at {event['timestamp']}")

        return is_anomaly

    def get_normal_activity_hours(self, event_type: str = None) -> List[int]:
        """
        Get hours when activity is normally observed

        Args:
            event_type: Filter by event type (None for all)

        Returns:
            List of hours (0-23) when activity is normal
        """
        if event_type:
            hour_counts = defaultdict(int)
            for hour, events in self.time_patterns.items():
                count = events.count(event_type)
                hour_counts[hour] = count

            # Return hours with above-average activity
            avg = np.mean(list(hour_counts.values())) if hour_counts else 0
            return [h for h, c in hour_counts.items() if c > avg]
        else:
            return list(self.time_patterns.keys())

    def is_unusual_time(self, event_type: str, hour: int = None) -> bool:
        """
        Check if event at given time is unusual

        Args:
            event_type: Type of event
            hour: Hour of day (current hour if None)

        Returns:
            True if unusual
        """
        if hour is None:
            hour = datetime.now().hour

        normal_hours = self.get_normal_activity_hours(event_type)

        if not normal_hours:
            return False  # No data yet

        return hour not in normal_hours

    def get_person_normal_times(self, person_id: str) -> List[int]:
        """
        Get normal appearance times for a person

        Args:
            person_id: Person identifier

        Returns:
            List of hours when person normally appears
        """
        if person_id not in self.person_behaviors:
            return []

        usual_times = self.person_behaviors[person_id]['usual_times']

        if not usual_times:
            return []

        # Return hours with above-average appearances
        avg = np.mean(list(usual_times.values()))
        return [h for h, c in usual_times.items() if c > avg]

    def is_person_unusual(self, person_id: str, hour: int = None) -> bool:
        """
        Check if person appearing at this time is unusual

        Args:
            person_id: Person identifier
            hour: Hour of day (current hour if None)

        Returns:
            True if unusual
        """
        if hour is None:
            hour = datetime.now().hour

        normal_times = self.get_person_normal_times(person_id)

        if not normal_times:
            return False  # No data yet

        return hour not in normal_times

    def get_statistics(self) -> Dict:
        """Get behavioral analysis statistics"""
        return {
            'total_events': len(self.events_buffer),
            'total_people': len(self.person_behaviors),
            'total_anomalies': len(self.anomaly_history),
            'recent_anomalies': list(self.anomaly_history)[-10:],
            'activity_by_type': dict(self.activity_patterns),
            'busiest_hours': sorted(
                self.time_patterns.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:5]
        }

    def get_person_profile(self, person_id: str) -> Dict:
        """Get detailed behavior profile for a person"""
        if person_id not in self.person_behaviors:
            return None

        behavior = self.person_behaviors[person_id]

        return {
            'person_id': person_id,
            'first_seen': behavior['first_seen'],
            'last_seen': behavior['last_seen'],
            'total_appearances': behavior['total_appearances'],
            'usual_times': dict(behavior['usual_times']),
            'normal_hours': self.get_person_normal_times(person_id)
        }

    def save_patterns(self):
        """Save learned patterns to disk"""
        data = {
            'time_patterns': dict(self.time_patterns),
            'daily_patterns': dict(self.daily_patterns),
            'activity_patterns': dict(self.activity_patterns),
            'person_behaviors': dict(self.person_behaviors),
        }

        # Save patterns
        with open(os.path.join(self.storage_dir, 'patterns.json'), 'w') as f:
            json.dump(data, f, indent=2, default=str)

        # Save anomaly detector
        if self.anomaly_detector:
            with open(os.path.join(self.storage_dir, 'anomaly_model.pkl'), 'wb') as f:
                pickle.dump({
                    'detector': self.anomaly_detector,
                    'scaler': self.scaler
                }, f)

        logger.info("Behavioral patterns saved")

    def load_patterns(self):
        """Load learned patterns from disk"""
        patterns_file = os.path.join(self.storage_dir, 'patterns.json')

        if os.path.exists(patterns_file):
            try:
                with open(patterns_file, 'r') as f:
                    data = json.load(f)

                self.time_patterns = defaultdict(list, data.get('time_patterns', {}))
                self.daily_patterns = defaultdict(list, data.get('daily_patterns', {}))
                self.activity_patterns = defaultdict(int, data.get('activity_patterns', {}))
                self.person_behaviors = defaultdict(
                    lambda: {
                        'usual_times': defaultdict(int),
                        'usual_paths': [],
                        'dwell_times': [],
                        'first_seen': None,
                        'last_seen': None,
                        'total_appearances': 0
                    },
                    data.get('person_behaviors', {})
                )

                logger.info("Loaded behavioral patterns")
            except Exception as e:
                logger.error(f"Failed to load patterns: {e}")

        # Load anomaly detector
        model_file = os.path.join(self.storage_dir, 'anomaly_model.pkl')
        if os.path.exists(model_file):
            try:
                with open(model_file, 'rb') as f:
                    data = pickle.load(f)
                    self.anomaly_detector = data['detector']
                    self.scaler = data['scaler']
                logger.info("Loaded anomaly detection model")
            except Exception as e:
                logger.error(f"Failed to load anomaly model: {e}")
