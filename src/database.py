"""
Database module for storing historical data and analytics
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import func, and_, or_
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)

Base = declarative_base()


class Detection(Base):
    """Detection events table"""
    __tablename__ = 'detections'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    object_type = Column(String(50), index=True)  # person, car, etc.
    object_id = Column(String(100), index=True)  # Tracking ID
    confidence = Column(Float)
    bbox = Column(JSON)  # Bounding box coordinates
    metadata = Column(JSON)  # Additional data (color, speed, etc.)
    camera_id = Column(String(50), index=True)
    is_anomaly = Column(Boolean, default=False)


class PersonAppearance(Base):
    """Person appearance tracking"""
    __tablename__ = 'person_appearances'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    person_id = Column(String(100), index=True)
    person_name = Column(String(100))
    confidence = Column(Float)
    duration = Column(Integer)  # Duration in seconds
    location = Column(JSON)  # Location in frame
    camera_id = Column(String(50))
    is_recognized = Column(Boolean, default=False)
    is_unusual_time = Column(Boolean, default=False)


class VehicleRecord(Base):
    """Vehicle tracking records"""
    __tablename__ = 'vehicle_records'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    vehicle_id = Column(String(100), index=True)
    vehicle_type = Column(String(50))  # car, truck, motorcycle
    color = Column(String(50), index=True)
    speed = Column(Float)  # Speed in km/h
    direction = Column(String(20))  # Direction of travel
    camera_id = Column(String(50))
    metadata = Column(JSON)


class LicensePlate(Base):
    """License plate recognition records"""
    __tablename__ = 'license_plates'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    plate_number = Column(String(20), index=True)  # License plate number
    confidence = Column(Float)  # OCR confidence
    vehicle_type = Column(String(50))  # Associated vehicle type
    vehicle_color = Column(String(50))  # Associated vehicle color
    vehicle_id = Column(String(100))  # Link to vehicle record
    country = Column(String(10))  # Country/region code
    camera_id = Column(String(50))
    bbox = Column(JSON)  # Plate bounding box
    raw_text = Column(String(50))  # Raw OCR text before cleaning
    metadata = Column(JSON)  # Additional data


class Anomaly(Base):
    """Anomaly detection records"""
    __tablename__ = 'anomalies'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    anomaly_type = Column(String(50), index=True)
    severity = Column(Float)  # 0.0 to 1.0
    description = Column(Text)
    related_objects = Column(JSON)
    camera_id = Column(String(50))
    resolved = Column(Boolean, default=False)


class ActivityLog(Base):
    """General activity logging"""
    __tablename__ = 'activity_log'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    activity_type = Column(String(50), index=True)
    count = Column(Integer, default=1)
    hour = Column(Integer, index=True)
    day_of_week = Column(Integer, index=True)
    metadata = Column(JSON)


class DatabaseManager:
    """Manage database operations"""

    def __init__(self, db_url='sqlite:///data/camera_system.db'):
        """
        Initialize database manager

        Args:
            db_url: Database URL
        """
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)

        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)

        logger.info(f"Database initialized: {db_url}")

    def get_session(self):
        """Get database session"""
        return self.Session()

    def add_detection(self, object_type: str, object_id: str, confidence: float,
                     bbox: List, metadata: Dict, camera_id: str = 'default',
                     is_anomaly: bool = False):
        """Add detection record"""
        session = self.get_session()
        try:
            detection = Detection(
                object_type=object_type,
                object_id=object_id,
                confidence=confidence,
                bbox=bbox,
                metadata=metadata,
                camera_id=camera_id,
                is_anomaly=is_anomaly
            )
            session.add(detection)
            session.commit()
        except Exception as e:
            logger.error(f"Failed to add detection: {e}")
            session.rollback()
        finally:
            session.close()

    def add_person_appearance(self, person_id: str, person_name: str, confidence: float,
                            location: Dict, camera_id: str = 'default',
                            is_recognized: bool = True, is_unusual_time: bool = False):
        """Add person appearance record"""
        session = self.get_session()
        try:
            appearance = PersonAppearance(
                person_id=person_id,
                person_name=person_name,
                confidence=confidence,
                location=location,
                camera_id=camera_id,
                is_recognized=is_recognized,
                is_unusual_time=is_unusual_time
            )
            session.add(appearance)
            session.commit()
        except Exception as e:
            logger.error(f"Failed to add person appearance: {e}")
            session.rollback()
        finally:
            session.close()

    def add_vehicle_record(self, vehicle_id: str, vehicle_type: str, color: str,
                          speed: float, camera_id: str = 'default', metadata: Dict = None):
        """Add vehicle record"""
        session = self.get_session()
        try:
            vehicle = VehicleRecord(
                vehicle_id=vehicle_id,
                vehicle_type=vehicle_type,
                color=color,
                speed=speed,
                camera_id=camera_id,
                metadata=metadata or {}
            )
            session.add(vehicle)
            session.commit()
        except Exception as e:
            logger.error(f"Failed to add vehicle record: {e}")
            session.rollback()
        finally:
            session.close()

    def add_license_plate(self, plate_number: str, confidence: float,
                         vehicle_type: str = None, vehicle_color: str = None,
                         vehicle_id: str = None, country: str = None,
                         camera_id: str = 'default', bbox: Dict = None,
                         raw_text: str = None, metadata: Dict = None):
        """Add license plate record"""
        session = self.get_session()
        try:
            plate = LicensePlate(
                plate_number=plate_number,
                confidence=confidence,
                vehicle_type=vehicle_type,
                vehicle_color=vehicle_color,
                vehicle_id=vehicle_id,
                country=country,
                camera_id=camera_id,
                bbox=bbox or {},
                raw_text=raw_text,
                metadata=metadata or {}
            )
            session.add(plate)
            session.commit()
        except Exception as e:
            logger.error(f"Failed to add license plate: {e}")
            session.rollback()
        finally:
            session.close()

    def add_anomaly(self, anomaly_type: str, severity: float, description: str,
                   related_objects: List, camera_id: str = 'default'):
        """Add anomaly record"""
        session = self.get_session()
        try:
            anomaly = Anomaly(
                anomaly_type=anomaly_type,
                severity=severity,
                description=description,
                related_objects=related_objects,
                camera_id=camera_id
            )
            session.add(anomaly)
            session.commit()
        except Exception as e:
            logger.error(f"Failed to add anomaly: {e}")
            session.rollback()
        finally:
            session.close()

    def log_activity(self, activity_type: str, count: int = 1, metadata: Dict = None):
        """Log activity"""
        timestamp = datetime.now()
        session = self.get_session()
        try:
            log = ActivityLog(
                activity_type=activity_type,
                count=count,
                hour=timestamp.hour,
                day_of_week=timestamp.weekday(),
                metadata=metadata or {}
            )
            session.add(log)
            session.commit()
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            session.rollback()
        finally:
            session.close()

    def get_detections(self, hours: int = 24, object_type: str = None,
                      camera_id: str = None) -> List[Dict]:
        """Get recent detections"""
        session = self.get_session()
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            query = session.query(Detection).filter(Detection.timestamp >= cutoff)

            if object_type:
                query = query.filter(Detection.object_type == object_type)
            if camera_id:
                query = query.filter(Detection.camera_id == camera_id)

            detections = query.order_by(Detection.timestamp.desc()).limit(1000).all()

            return [
                {
                    'id': d.id,
                    'timestamp': d.timestamp.isoformat(),
                    'object_type': d.object_type,
                    'object_id': d.object_id,
                    'confidence': d.confidence,
                    'bbox': d.bbox,
                    'metadata': d.metadata,
                    'is_anomaly': d.is_anomaly
                }
                for d in detections
            ]
        finally:
            session.close()

    def get_person_history(self, person_id: str, days: int = 30) -> List[Dict]:
        """Get person appearance history"""
        session = self.get_session()
        try:
            cutoff = datetime.now() - timedelta(days=days)
            appearances = session.query(PersonAppearance).filter(
                and_(
                    PersonAppearance.person_id == person_id,
                    PersonAppearance.timestamp >= cutoff
                )
            ).order_by(PersonAppearance.timestamp.desc()).all()

            return [
                {
                    'timestamp': a.timestamp.isoformat(),
                    'person_name': a.person_name,
                    'confidence': a.confidence,
                    'is_unusual_time': a.is_unusual_time
                }
                for a in appearances
            ]
        finally:
            session.close()

    def get_vehicle_statistics(self, hours: int = 24) -> Dict:
        """Get vehicle statistics"""
        session = self.get_session()
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            vehicles = session.query(VehicleRecord).filter(
                VehicleRecord.timestamp >= cutoff
            ).all()

            if not vehicles:
                return {
                    'total_vehicles': 0,
                    'average_speed': 0,
                    'color_distribution': {},
                    'type_distribution': {}
                }

            speeds = [v.speed for v in vehicles if v.speed]
            colors = [v.color for v in vehicles if v.color]
            types = [v.vehicle_type for v in vehicles if v.vehicle_type]

            from collections import Counter

            return {
                'total_vehicles': len(vehicles),
                'average_speed': sum(speeds) / len(speeds) if speeds else 0,
                'max_speed': max(speeds) if speeds else 0,
                'color_distribution': dict(Counter(colors)),
                'type_distribution': dict(Counter(types))
            }
        finally:
            session.close()

    def get_anomalies(self, hours: int = 24, unresolved_only: bool = True) -> List[Dict]:
        """Get anomaly records"""
        session = self.get_session()
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            query = session.query(Anomaly).filter(Anomaly.timestamp >= cutoff)

            if unresolved_only:
                query = query.filter(Anomaly.resolved == False)

            anomalies = query.order_by(Anomaly.timestamp.desc()).all()

            return [
                {
                    'id': a.id,
                    'timestamp': a.timestamp.isoformat(),
                    'type': a.anomaly_type,
                    'severity': a.severity,
                    'description': a.description,
                    'related_objects': a.related_objects,
                    'resolved': a.resolved
                }
                for a in anomalies
            ]
        finally:
            session.close()

    def get_hourly_activity(self, days: int = 7) -> Dict:
        """Get hourly activity distribution"""
        session = self.get_session()
        try:
            cutoff = datetime.now() - timedelta(days=days)
            activities = session.query(
                ActivityLog.hour,
                func.sum(ActivityLog.count).label('total')
            ).filter(
                ActivityLog.timestamp >= cutoff
            ).group_by(ActivityLog.hour).all()

            return {hour: total for hour, total in activities}
        finally:
            session.close()

    def get_daily_activity(self, days: int = 30) -> Dict:
        """Get daily activity distribution"""
        session = self.get_session()
        try:
            cutoff = datetime.now() - timedelta(days=days)
            activities = session.query(
                ActivityLog.day_of_week,
                func.sum(ActivityLog.count).label('total')
            ).filter(
                ActivityLog.timestamp >= cutoff
            ).group_by(ActivityLog.day_of_week).all()

            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            return {day_names[day]: total for day, total in activities}
        finally:
            session.close()

    def cleanup_old_data(self, days: int = 90):
        """Remove data older than specified days"""
        session = self.get_session()
        try:
            cutoff = datetime.now() - timedelta(days=days)

            # Clean up detections
            session.query(Detection).filter(Detection.timestamp < cutoff).delete()
            # Clean up person appearances
            session.query(PersonAppearance).filter(PersonAppearance.timestamp < cutoff).delete()
            # Clean up vehicle records
            session.query(VehicleRecord).filter(VehicleRecord.timestamp < cutoff).delete()
            # Keep anomalies longer
            # Clean up activity log
            session.query(ActivityLog).filter(ActivityLog.timestamp < cutoff).delete()

            session.commit()
            logger.info(f"Cleaned up data older than {days} days")
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            session.rollback()
        finally:
            session.close()
