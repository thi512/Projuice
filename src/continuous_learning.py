"""
Continuous Learning Orchestrator
Coordinates all AI systems to continuously learn and improve
"""
import logging
import time
from datetime import datetime, timedelta
from threading import Thread
import schedule
from typing import Dict, List

logger = logging.getLogger(__name__)


class ContinuousLearningSystem:
    """
    Orchestrates continuous learning across all AI systems
    Always looking for new patterns to learn
    """

    def __init__(self, face_recognition_system, behavioral_engine,
                 analytics_engine, database_manager):
        """
        Initialize continuous learning system

        Args:
            face_recognition_system: Face recognition AI
            behavioral_engine: Behavioral analysis engine
            analytics_engine: Advanced analytics
            database_manager: Database manager
        """
        self.face_ai = face_recognition_system
        self.behavior = behavioral_engine
        self.analytics = analytics_engine
        self.db = database_manager

        self.is_running = False
        self.learning_thread = None

        # Learning parameters
        self.learning_tasks = []
        self.last_pattern_learn = None
        self.last_face_learn = None
        self.last_behavior_update = None

        # Learning intervals
        self.face_learning_interval = 3600  # 1 hour
        self.pattern_learning_interval = 7200  # 2 hours
        self.behavior_update_interval = 1800  # 30 minutes

        logger.info("Continuous learning system initialized")

    def start(self):
        """Start continuous learning"""
        if self.is_running:
            logger.warning("Continuous learning already running")
            return

        self.is_running = True

        # Schedule learning tasks
        schedule.every(30).minutes.do(self._auto_learn_faces)
        schedule.every(1).hours.do(self._update_behavioral_patterns)
        schedule.every(2).hours.do(self._learn_new_patterns)
        schedule.every(6).hours.do(self._optimize_models)
        schedule.every(1).days.do(self._cleanup_old_data)

        # Start background thread
        self.learning_thread = Thread(target=self._learning_loop, daemon=True)
        self.learning_thread.start()

        logger.info("Continuous learning started")

    def stop(self):
        """Stop continuous learning"""
        self.is_running = False
        if self.learning_thread:
            self.learning_thread.join(timeout=5.0)
        logger.info("Continuous learning stopped")

    def _learning_loop(self):
        """Main learning loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in learning loop: {e}")

    def _auto_learn_faces(self):
        """
        Automatically learn frequently appearing unknown faces

        This learns faces that appear regularly but haven't been identified
        """
        logger.info("Running auto face learning...")

        try:
            # Auto-learn faces that appear frequently
            self.face_ai.auto_learn_frequent_unknowns(min_appearances=5)

            self.last_face_learn = datetime.now()
            logger.info("Auto face learning completed")

        except Exception as e:
            logger.error(f"Face learning failed: {e}")

    def _update_behavioral_patterns(self):
        """
        Update normal behavior patterns

        This learns what's normal activity at different times
        """
        logger.info("Updating behavioral patterns...")

        try:
            # Train/retrain anomaly detection model
            success = self.behavior.learn_normal_behavior()

            if success:
                self.last_behavior_update = datetime.now()
                logger.info("Behavioral patterns updated successfully")
            else:
                logger.warning("Not enough data to update behavioral patterns")

        except Exception as e:
            logger.error(f"Behavioral pattern update failed: {e}")

    def _learn_new_patterns(self):
        """
        Discover and learn new patterns

        This is the "always trying to learn" component that looks for:
        - Time-based patterns
        - Frequency patterns
        - Correlation patterns
        """
        logger.info("Looking for new patterns to learn...")

        try:
            discoveries = []

            # 1. Learn hourly activity patterns
            hourly_patterns = self._analyze_hourly_patterns()
            if hourly_patterns:
                discoveries.append(f"Learned hourly activity pattern: {hourly_patterns}")

            # 2. Learn person-specific patterns
            person_patterns = self._analyze_person_patterns()
            if person_patterns:
                discoveries.extend(person_patterns)

            # 3. Learn vehicle patterns
            vehicle_patterns = self._analyze_vehicle_patterns()
            if vehicle_patterns:
                discoveries.extend(vehicle_patterns)

            # 4. Learn correlation patterns
            correlations = self._find_correlations()
            if correlations:
                discoveries.extend(correlations)

            if discoveries:
                logger.info(f"New patterns learned: {len(discoveries)}")
                for discovery in discoveries[:5]:  # Log first 5
                    logger.info(f"  - {discovery}")
            else:
                logger.info("No new patterns discovered this cycle")

            self.last_pattern_learn = datetime.now()

        except Exception as e:
            logger.error(f"Pattern learning failed: {e}")

    def _analyze_hourly_patterns(self) -> str:
        """Analyze hourly activity patterns"""
        try:
            hourly_data = self.db.get_hourly_activity(days=7)

            if not hourly_data:
                return None

            # Find peak hours
            peak_hour = max(hourly_data, key=hourly_data.get)
            quiet_hour = min(hourly_data, key=hourly_data.get)

            return f"Peak activity at {peak_hour}:00, quietest at {quiet_hour}:00"

        except Exception as e:
            logger.error(f"Hourly pattern analysis failed: {e}")
            return None

    def _analyze_person_patterns(self) -> List[str]:
        """Analyze patterns for each known person"""
        discoveries = []

        try:
            known_people = self.face_ai.get_known_people()

            for person in known_people:
                person_id = person['person_id']
                profile = self.behavior.get_person_profile(person_id)

                if profile and profile['total_appearances'] > 10:
                    normal_hours = profile.get('normal_hours', [])

                    if normal_hours:
                        hour_range = f"{min(normal_hours)}:00-{max(normal_hours)}:00"
                        discoveries.append(
                            f"{person['name']} typically appears between {hour_range}"
                        )

        except Exception as e:
            logger.error(f"Person pattern analysis failed: {e}")

        return discoveries

    def _analyze_vehicle_patterns(self) -> List[str]:
        """Analyze vehicle patterns"""
        discoveries = []

        try:
            # Get vehicle statistics
            vehicle_stats = self.db.get_vehicle_statistics(hours=168)  # Last week

            if vehicle_stats['total_vehicles'] > 50:
                avg_speed = vehicle_stats['average_speed']
                discoveries.append(
                    f"Average vehicle speed: {avg_speed:.1f} km/h ({vehicle_stats['total_vehicles']} vehicles)"
                )

                # Most common colors
                colors = vehicle_stats.get('color_distribution', {})
                if colors:
                    most_common = max(colors, key=colors.get)
                    discoveries.append(f"Most common vehicle color: {most_common}")

        except Exception as e:
            logger.error(f"Vehicle pattern analysis failed: {e}")

        return discoveries

    def _find_correlations(self) -> List[str]:
        """Find correlations between different events"""
        discoveries = []

        try:
            # Find correlations between time and activity
            hourly_dist = self.analytics.time_analyzer.get_hourly_distribution()

            if hourly_dist:
                busy_hours = [h for h, c in hourly_dist.items() if c > sum(hourly_dist.values()) / len(hourly_dist)]

                if busy_hours:
                    discoveries.append(
                        f"High activity correlation with hours: {sorted(busy_hours)}"
                    )

        except Exception as e:
            logger.error(f"Correlation analysis failed: {e}")

        return discoveries

    def _optimize_models(self):
        """
        Optimize ML models based on learned data

        This periodically retrains models with accumulated data
        """
        logger.info("Optimizing ML models...")

        try:
            # Retrain behavioral model with all data
            self.behavior.learn_normal_behavior()

            # Consolidate face encodings
            self._consolidate_face_encodings()

            logger.info("Model optimization completed")

        except Exception as e:
            logger.error(f"Model optimization failed: {e}")

    def _consolidate_face_encodings(self):
        """Consolidate multiple face encodings per person"""
        try:
            for person_id, person_data in self.face_ai.known_faces.items():
                encodings = person_data['encodings']

                # If we have many encodings, keep only the most representative ones
                if len(encodings) > 20:
                    # Keep 10 most diverse encodings
                    # This is a simple approach - could be more sophisticated
                    import numpy as np
                    from sklearn.cluster import KMeans

                    encodings_array = np.array(encodings)
                    kmeans = KMeans(n_clusters=10, random_state=42)
                    kmeans.fit(encodings_array)

                    # Keep cluster centers
                    person_data['encodings'] = kmeans.cluster_centers_.tolist()

                    logger.info(f"Consolidated encodings for {person_data['name']}: {len(encodings)} -> 10")

            self.face_ai.save_known_faces()

        except Exception as e:
            logger.error(f"Face encoding consolidation failed: {e}")

    def _cleanup_old_data(self):
        """Cleanup old data from database"""
        logger.info("Cleaning up old data...")

        try:
            self.db.cleanup_old_data(days=90)
            logger.info("Old data cleanup completed")

        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")

    def get_learning_status(self) -> Dict:
        """Get status of learning system"""
        return {
            'is_running': self.is_running,
            'last_face_learn': self.last_face_learn.isoformat() if self.last_face_learn else None,
            'last_pattern_learn': self.last_pattern_learn.isoformat() if self.last_pattern_learn else None,
            'last_behavior_update': self.last_behavior_update.isoformat() if self.last_behavior_update else None,
            'known_people': len(self.face_ai.known_faces),
            'total_events': len(self.behavior.events_buffer)
        }

    def force_learning_cycle(self):
        """Force an immediate learning cycle (manual trigger)"""
        logger.info("Forcing immediate learning cycle...")

        self._auto_learn_faces()
        self._update_behavioral_patterns()
        self._learn_new_patterns()

        logger.info("Learning cycle completed")

    def suggest_next_learning_task(self) -> str:
        """
        Suggest what the system should learn next

        This is the "always trying to learn something new" feature
        """
        suggestions = []

        # Check if we have unknown faces to learn
        unknown_count = len(self.face_ai.unknown_faces)
        if unknown_count > 5:
            suggestions.append(f"Learn {unknown_count} frequently appearing unknown faces")

        # Check if we have enough data for new patterns
        event_count = len(self.behavior.events_buffer)
        if event_count > 1000 and not self.behavior.anomaly_detector:
            suggestions.append("Train anomaly detection model (sufficient data collected)")

        # Check for new correlation opportunities
        hourly_data = self.db.get_hourly_activity(days=7)
        if hourly_data and len(hourly_data) >= 20:
            suggestions.append("Analyze time-based correlations")

        # Suggest speed pattern analysis
        vehicle_stats = self.db.get_vehicle_statistics(hours=168)
        if vehicle_stats['total_vehicles'] > 100:
            suggestions.append("Analyze vehicle speed patterns and trends")

        if not suggestions:
            return "System is up to date - monitoring for new learning opportunities"

        return "; ".join(suggestions)
