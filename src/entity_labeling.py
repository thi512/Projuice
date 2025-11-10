"""
Entity Labeling System
Allows labeling of detected faces, vehicles, and other entities
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EntityLabeling:
    """Manage labeling of detected entities (faces, vehicles, etc.)"""

    def __init__(self, database_manager, face_ai=None):
        """
        Initialize entity labeling system

        Args:
            database_manager: DatabaseManager instance
            face_ai: FaceRecognitionSystem instance
        """
        self.db = database_manager
        self.face_ai = face_ai

    def get_unlabeled_faces(self, min_appearances: int = 3, days: int = 30) -> List[Dict]:
        """
        Get faces that appear frequently but are unlabeled

        Args:
            min_appearances: Minimum number of appearances to be considered
            days: Look back this many days

        Returns:
            List of unlabeled face records
        """
        if not self.db:
            return []

        try:
            session = self.db.Session()
            cutoff_date = datetime.now() - timedelta(days=days)

            # Get all person appearances
            from sqlalchemy import func
            query = session.query(
                self.db.PersonAppearance.person_name,
                func.count(self.db.PersonAppearance.id).label('count'),
                func.max(self.db.PersonAppearance.timestamp).label('last_seen'),
                func.min(self.db.PersonAppearance.timestamp).label('first_seen')
            ).filter(
                self.db.PersonAppearance.timestamp >= cutoff_date,
                self.db.PersonAppearance.person_name.like('Unknown%')
            ).group_by(
                self.db.PersonAppearance.person_name
            ).having(
                func.count(self.db.PersonAppearance.id) >= min_appearances
            ).order_by(
                func.count(self.db.PersonAppearance.id).desc()
            )

            results = []
            for row in query.all():
                results.append({
                    'person_id': row.person_name,
                    'appearances': row.count,
                    'first_seen': row.first_seen.isoformat(),
                    'last_seen': row.last_seen.isoformat(),
                    'type': 'face'
                })

            session.close()
            return results

        except Exception as e:
            logger.error(f"Failed to get unlabeled faces: {e}")
            return []

    def get_frequent_vehicles(self, min_appearances: int = 5, days: int = 30) -> List[Dict]:
        """
        Get vehicles that appear frequently

        Args:
            min_appearances: Minimum number of appearances
            days: Look back this many days

        Returns:
            List of frequent vehicle records
        """
        if not self.db:
            return []

        try:
            session = self.db.Session()
            cutoff_date = datetime.now() - timedelta(days=days)

            # Get vehicles by license plate or vehicle ID
            from sqlalchemy import func, or_

            # Query license plates
            lpr_query = session.query(
                self.db.LicensePlate.plate_number.label('identifier'),
                self.db.LicensePlate.vehicle_type,
                self.db.LicensePlate.vehicle_color,
                func.count(self.db.LicensePlate.id).label('count'),
                func.max(self.db.LicensePlate.timestamp).label('last_seen'),
                func.min(self.db.LicensePlate.timestamp).label('first_seen'),
                func.avg(self.db.LicensePlate.confidence).label('avg_confidence')
            ).filter(
                self.db.LicensePlate.timestamp >= cutoff_date,
                self.db.LicensePlate.plate_number.isnot(None)
            ).group_by(
                self.db.LicensePlate.plate_number,
                self.db.LicensePlate.vehicle_type,
                self.db.LicensePlate.vehicle_color
            ).having(
                func.count(self.db.LicensePlate.id) >= min_appearances
            )

            results = []
            for row in lpr_query.all():
                # Check if this plate has a label
                label = self._get_vehicle_label(row.identifier)

                results.append({
                    'identifier': row.identifier,
                    'type': 'vehicle',
                    'vehicle_type': row.vehicle_type,
                    'color': row.vehicle_color,
                    'appearances': row.count,
                    'first_seen': row.first_seen.isoformat(),
                    'last_seen': row.last_seen.isoformat(),
                    'confidence': float(row.avg_confidence) if row.avg_confidence else 0,
                    'label': label,
                    'is_labeled': label is not None
                })

            session.close()
            return sorted(results, key=lambda x: x['appearances'], reverse=True)

        except Exception as e:
            logger.error(f"Failed to get frequent vehicles: {e}")
            return []

    def label_face(self, person_id: str, new_name: str, notes: str = '') -> bool:
        """
        Label a face with a new name

        Args:
            person_id: Person ID (e.g., "Unknown_1")
            new_name: New name for the person
            notes: Optional notes

        Returns:
            True if successful
        """
        try:
            # Update database records
            if self.db:
                session = self.db.Session()

                # Update all appearances with this person_id
                session.query(self.db.PersonAppearance).filter(
                    self.db.PersonAppearance.person_name == person_id
                ).update({
                    'person_name': new_name,
                    'is_recognized': True
                })

                session.commit()
                session.close()

            # Update face recognition system if available
            if self.face_ai:
                # Try to update known faces
                # This depends on the face_ai implementation
                pass

            logger.info(f"Labeled face {person_id} as '{new_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to label face: {e}")
            return False

    def label_vehicle(self, identifier: str, label: str, notes: str = '') -> bool:
        """
        Label a vehicle

        Args:
            identifier: Vehicle identifier (license plate or ID)
            label: Label for the vehicle (e.g., "My Car", "Neighbor's Truck")
            notes: Optional notes

        Returns:
            True if successful
        """
        try:
            if not self.db:
                return False

            session = self.db.Session()

            # Create or update vehicle label
            # Note: We need to add a VehicleLabel table to the database schema

            # For now, store in metadata of license plate records
            session.query(self.db.LicensePlate).filter(
                self.db.LicensePlate.plate_number == identifier
            ).update({
                'metadata': {
                    'label': label,
                    'notes': notes,
                    'labeled_at': datetime.now().isoformat()
                }
            }, synchronize_session=False)

            session.commit()
            session.close()

            logger.info(f"Labeled vehicle {identifier} as '{label}'")
            return True

        except Exception as e:
            logger.error(f"Failed to label vehicle: {e}")
            return False

    def _get_vehicle_label(self, identifier: str) -> Optional[str]:
        """
        Get label for a vehicle

        Args:
            identifier: Vehicle identifier

        Returns:
            Label or None
        """
        try:
            if not self.db:
                return None

            session = self.db.Session()

            record = session.query(self.db.LicensePlate).filter(
                self.db.LicensePlate.plate_number == identifier
            ).first()

            session.close()

            if record and record.metadata:
                if isinstance(record.metadata, dict):
                    return record.metadata.get('label')

        except Exception as e:
            logger.error(f"Failed to get vehicle label: {e}")

        return None

    def get_labeled_entities(self, entity_type: str = 'all') -> List[Dict]:
        """
        Get all labeled entities

        Args:
            entity_type: 'face', 'vehicle', or 'all'

        Returns:
            List of labeled entities
        """
        labeled = []

        if entity_type in ['face', 'all']:
            labeled.extend(self._get_labeled_faces())

        if entity_type in ['vehicle', 'all']:
            labeled.extend(self._get_labeled_vehicles())

        return labeled

    def _get_labeled_faces(self) -> List[Dict]:
        """Get all labeled faces"""
        if not self.db:
            return []

        try:
            session = self.db.Session()

            # Get unique labeled people
            from sqlalchemy import func
            query = session.query(
                self.db.PersonAppearance.person_name,
                func.count(self.db.PersonAppearance.id).label('appearances'),
                func.max(self.db.PersonAppearance.timestamp).label('last_seen')
            ).filter(
                self.db.PersonAppearance.is_recognized == True,
                ~self.db.PersonAppearance.person_name.like('Unknown%')
            ).group_by(
                self.db.PersonAppearance.person_name
            )

            results = []
            for row in query.all():
                results.append({
                    'name': row.person_name,
                    'type': 'face',
                    'appearances': row.appearances,
                    'last_seen': row.last_seen.isoformat() if row.last_seen else None
                })

            session.close()
            return results

        except Exception as e:
            logger.error(f"Failed to get labeled faces: {e}")
            return []

    def _get_labeled_vehicles(self) -> List[Dict]:
        """Get all labeled vehicles"""
        if not self.db:
            return []

        try:
            session = self.db.Session()

            # Get vehicles with labels in metadata
            query = session.query(self.db.LicensePlate).filter(
                self.db.LicensePlate.metadata.isnot(None)
            )

            labeled_vehicles = {}
            for record in query.all():
                if isinstance(record.metadata, dict) and 'label' in record.metadata:
                    plate = record.plate_number
                    if plate not in labeled_vehicles:
                        labeled_vehicles[plate] = {
                            'identifier': plate,
                            'type': 'vehicle',
                            'label': record.metadata['label'],
                            'notes': record.metadata.get('notes', ''),
                            'vehicle_type': record.vehicle_type,
                            'color': record.vehicle_color,
                            'appearances': 1,
                            'last_seen': record.timestamp.isoformat()
                        }
                    else:
                        labeled_vehicles[plate]['appearances'] += 1

            session.close()
            return list(labeled_vehicles.values())

        except Exception as e:
            logger.error(f"Failed to get labeled vehicles: {e}")
            return []

    def remove_label(self, identifier: str, entity_type: str) -> bool:
        """
        Remove a label from an entity

        Args:
            identifier: Entity identifier
            entity_type: 'face' or 'vehicle'

        Returns:
            True if successful
        """
        try:
            if entity_type == 'face':
                return self._remove_face_label(identifier)
            elif entity_type == 'vehicle':
                return self._remove_vehicle_label(identifier)
            else:
                return False

        except Exception as e:
            logger.error(f"Failed to remove label: {e}")
            return False

    def _remove_face_label(self, person_name: str) -> bool:
        """Remove face label (set back to Unknown)"""
        if not self.db:
            return False

        session = self.db.Session()

        # Generate new unknown ID
        new_id = f"Unknown_{person_name}"

        session.query(self.db.PersonAppearance).filter(
            self.db.PersonAppearance.person_name == person_name
        ).update({
            'person_name': new_id,
            'is_recognized': False
        })

        session.commit()
        session.close()

        logger.info(f"Removed label for {person_name}")
        return True

    def _remove_vehicle_label(self, identifier: str) -> bool:
        """Remove vehicle label"""
        if not self.db:
            return False

        session = self.db.Session()

        session.query(self.db.LicensePlate).filter(
            self.db.LicensePlate.plate_number == identifier
        ).update({
            'metadata': None
        }, synchronize_session=False)

        session.commit()
        session.close()

        logger.info(f"Removed label for vehicle {identifier}")
        return True

    def get_entity_history(self, identifier: str, entity_type: str, days: int = 30) -> List[Dict]:
        """
        Get history of appearances for an entity

        Args:
            identifier: Entity identifier
            entity_type: 'face' or 'vehicle'
            days: Number of days to look back

        Returns:
            List of appearance records
        """
        if entity_type == 'face':
            return self._get_face_history(identifier, days)
        elif entity_type == 'vehicle':
            return self._get_vehicle_history(identifier, days)
        else:
            return []

    def _get_face_history(self, person_name: str, days: int) -> List[Dict]:
        """Get face appearance history"""
        if not self.db:
            return []

        try:
            session = self.db.Session()
            cutoff_date = datetime.now() - timedelta(days=days)

            query = session.query(self.db.PersonAppearance).filter(
                self.db.PersonAppearance.person_name == person_name,
                self.db.PersonAppearance.timestamp >= cutoff_date
            ).order_by(self.db.PersonAppearance.timestamp.desc())

            results = []
            for record in query.limit(100):
                results.append({
                    'timestamp': record.timestamp.isoformat(),
                    'confidence': record.confidence,
                    'is_unusual': record.is_unusual_time,
                    'camera_id': record.camera_id
                })

            session.close()
            return results

        except Exception as e:
            logger.error(f"Failed to get face history: {e}")
            return []

    def _get_vehicle_history(self, identifier: str, days: int) -> List[Dict]:
        """Get vehicle appearance history"""
        if not self.db:
            return []

        try:
            session = self.db.Session()
            cutoff_date = datetime.now() - timedelta(days=days)

            query = session.query(self.db.LicensePlate).filter(
                self.db.LicensePlate.plate_number == identifier,
                self.db.LicensePlate.timestamp >= cutoff_date
            ).order_by(self.db.LicensePlate.timestamp.desc())

            results = []
            for record in query.limit(100):
                results.append({
                    'timestamp': record.timestamp.isoformat(),
                    'confidence': record.confidence,
                    'vehicle_type': record.vehicle_type,
                    'color': record.vehicle_color,
                    'camera_id': record.camera_id
                })

            session.close()
            return results

        except Exception as e:
            logger.error(f"Failed to get vehicle history: {e}")
            return []
