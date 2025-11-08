"""
Chatbot Query Engine - Natural language interface for camera system
Allows users to ask questions and search video recordings intelligently
"""
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class ChatbotQueryEngine:
    """Natural language query engine for camera system"""

    def __init__(self, database_manager, config):
        """
        Initialize chatbot query engine

        Args:
            database_manager: DatabaseManager instance
            config: System configuration
        """
        self.db = database_manager
        self.config = config

        # Query patterns for natural language understanding
        self.patterns = self._build_query_patterns()

        # Entity extraction patterns
        self.time_patterns = {
            'today': lambda: datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
            'yesterday': lambda: (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
            'this week': lambda: datetime.now() - timedelta(days=7),
            'this month': lambda: datetime.now() - timedelta(days=30),
            'last hour': lambda: datetime.now() - timedelta(hours=1),
            'last (\d+) hours': lambda m: datetime.now() - timedelta(hours=int(m.group(1))),
            'last (\d+) minutes': lambda m: datetime.now() - timedelta(minutes=int(m.group(1))),
            'last (\d+) days': lambda m: datetime.now() - timedelta(days=int(m.group(1))),
        }

    def _build_query_patterns(self):
        """Build regex patterns for query understanding"""
        return {
            # Detection queries
            'person_detection': [
                r'(?:show|find|get|when).*(?:person|people|someone)',
                r'(?:who|anyone).*(?:detected|seen|appeared)',
                r'(?:visitor|delivery)',
            ],
            'vehicle_detection': [
                r'(?:show|find|get|when).*(?:car|vehicle|truck|bus)',
                r'(?:how many|count).*(?:car|vehicle)',
            ],
            'pet_detection': [
                r'(?:show|find|get|when).*(?:dog|cat|pet)',
                r'(?:my )?(?:dog|cat|pet)',
            ],
            'motion_detection': [
                r'(?:motion|movement|activity)',
                r'anything (?:moving|happening)',
            ],

            # Specific person queries
            'named_person': [
                r'(?:show|find|when).*(?:named|called) ([a-zA-Z]+)',
                r'person ([a-zA-Z]+)',
            ],

            # Vehicle-specific queries
            'vehicle_speed': [
                r'(?:speed|fast|slow).*(?:car|vehicle)',
                r'(?:car|vehicle).*(?:speed|fast|slow)',
            ],
            'vehicle_color': [
                r'(\w+) (?:car|vehicle|truck)',
                r'(?:car|vehicle|truck).*(\w+) color',
            ],

            # Time-based queries
            'recent': [
                r'(?:recent|latest|last)',
                r'in the (?:last|past)',
            ],

            # Count queries
            'count': [
                r'(?:how many|count|number of)',
            ],

            # Anomaly queries
            'anomaly': [
                r'(?:unusual|strange|anomaly|weird|suspicious)',
                r'anything (?:unusual|strange|wrong)',
            ],

            # Recording queries
            'recordings': [
                r'(?:show|find|get).*(?:recording|video|footage)',
                r'(?:recording|video|footage)',
            ],

            # License plate queries
            'license_plate': [
                r'(?:license|number) plate',
                r'plate (?:number|recognition)',
                r'(?:show|find).*(?:plate|tag)',
            ],
            'specific_plate': [
                r'plate (?:number )?([A-Z0-9]+)',
                r'([A-Z0-9]{3,10}).*plate',
            ],
        }

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process natural language query and return results

        Args:
            query: Natural language query string

        Returns:
            Dictionary with results and metadata
        """
        query_lower = query.lower().strip()

        logger.info(f"Processing query: {query}")

        # Extract time range
        time_range = self._extract_time_range(query_lower)

        # Determine query intent
        intent = self._determine_intent(query_lower)

        # Extract entities
        entities = self._extract_entities(query_lower, intent)

        # Execute query based on intent
        results = self._execute_query(intent, entities, time_range)

        # Format response
        response = self._format_response(intent, entities, results, time_range)

        return {
            'query': query,
            'intent': intent,
            'entities': entities,
            'time_range': time_range,
            'results': results,
            'response': response,
            'success': True
        }

    def _extract_time_range(self, query: str) -> Dict[str, Optional[datetime]]:
        """Extract time range from query"""
        start_time = None
        end_time = datetime.now()

        for pattern, time_func in self.time_patterns.items():
            match = re.search(pattern, query)
            if match:
                if callable(time_func):
                    if '(' in pattern:  # Pattern with capture group
                        start_time = time_func(match)
                    else:
                        start_time = time_func()
                break

        # Default to last 24 hours if no time specified
        if start_time is None:
            start_time = datetime.now() - timedelta(days=1)

        return {
            'start': start_time,
            'end': end_time
        }

    def _determine_intent(self, query: str) -> str:
        """Determine the primary intent of the query"""
        scores = {}

        for intent, patterns in self.patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query):
                    score += 1
            if score > 0:
                scores[intent] = score

        if not scores:
            return 'general_detection'

        # Return intent with highest score
        return max(scores, key=scores.get)

    def _extract_entities(self, query: str, intent: str) -> Dict[str, Any]:
        """Extract entities from query based on intent"""
        entities = {}

        # Extract person name
        if intent == 'named_person' or 'person' in query:
            name_match = re.search(r'(?:named|called|person) ([a-zA-Z]+)', query)
            if name_match:
                entities['person_name'] = name_match.group(1).capitalize()

        # Extract vehicle color
        if intent == 'vehicle_color' or 'color' in query:
            colors = ['red', 'blue', 'green', 'yellow', 'white', 'black', 'silver', 'gray', 'grey']
            for color in colors:
                if color in query:
                    entities['color'] = color
                    break

        # Extract object type
        if 'car' in query or 'vehicle' in query:
            entities['object_type'] = 'vehicle'
        elif 'person' in query or 'people' in query or 'someone' in query:
            entities['object_type'] = 'person'
        elif 'dog' in query or 'cat' in query or 'pet' in query:
            entities['object_type'] = 'pet'

        # Extract count request
        if re.search(r'how many|count|number', query):
            entities['wants_count'] = True

        # Extract license plate number
        if intent in ['license_plate', 'specific_plate']:
            # Look for alphanumeric sequences (3-10 characters)
            plate_match = re.search(r'\b([A-Z0-9]{3,10})\b', query.upper())
            if plate_match:
                entities['plate_number'] = plate_match.group(1)

        return entities

    def _execute_query(self, intent: str, entities: Dict, time_range: Dict) -> List[Dict]:
        """Execute database query based on intent and entities"""
        results = []

        try:
            if intent in ['person_detection', 'named_person']:
                results = self._query_person_detections(entities, time_range)

            elif intent == 'vehicle_detection':
                results = self._query_vehicle_detections(entities, time_range)

            elif intent == 'vehicle_speed':
                results = self._query_vehicle_speed(entities, time_range)

            elif intent == 'vehicle_color':
                results = self._query_vehicle_by_color(entities, time_range)

            elif intent == 'pet_detection':
                results = self._query_pet_detections(entities, time_range)

            elif intent == 'motion_detection':
                results = self._query_motion_events(time_range)

            elif intent == 'anomaly':
                results = self._query_anomalies(time_range)

            elif intent == 'recordings':
                results = self._query_recordings(time_range)

            elif intent in ['license_plate', 'specific_plate']:
                results = self._query_license_plates(entities, time_range)

            else:
                # General detection query
                results = self._query_all_detections(entities, time_range)

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            results = []

        return results

    def _query_person_detections(self, entities: Dict, time_range: Dict) -> List[Dict]:
        """Query person detections from database"""
        if not self.db:
            return []

        person_name = entities.get('person_name')

        # Query database
        session = self.db.Session()
        query = session.query(self.db.PersonAppearance)

        # Filter by time
        query = query.filter(
            self.db.PersonAppearance.timestamp >= time_range['start'],
            self.db.PersonAppearance.timestamp <= time_range['end']
        )

        # Filter by name if specified
        if person_name:
            query = query.filter(self.db.PersonAppearance.person_name == person_name)

        # Execute and format
        results = []
        for record in query.order_by(self.db.PersonAppearance.timestamp.desc()).limit(50):
            results.append({
                'type': 'person',
                'name': record.person_name,
                'timestamp': record.timestamp.isoformat(),
                'confidence': record.confidence,
                'is_recognized': record.is_recognized,
                'is_unusual': record.is_unusual_time
            })

        session.close()
        return results

    def _query_vehicle_detections(self, entities: Dict, time_range: Dict) -> List[Dict]:
        """Query vehicle detections"""
        if not self.db:
            return []

        session = self.db.Session()
        query = session.query(self.db.VehicleRecord)

        query = query.filter(
            self.db.VehicleRecord.timestamp >= time_range['start'],
            self.db.VehicleRecord.timestamp <= time_range['end']
        )

        results = []
        for record in query.order_by(self.db.VehicleRecord.timestamp.desc()).limit(50):
            results.append({
                'type': 'vehicle',
                'vehicle_type': record.vehicle_type,
                'color': record.color,
                'speed': record.speed,
                'timestamp': record.timestamp.isoformat()
            })

        session.close()
        return results

    def _query_vehicle_speed(self, entities: Dict, time_range: Dict) -> List[Dict]:
        """Query vehicles with speed data"""
        if not self.db:
            return []

        session = self.db.Session()
        query = session.query(self.db.VehicleRecord).filter(
            self.db.VehicleRecord.timestamp >= time_range['start'],
            self.db.VehicleRecord.timestamp <= time_range['end'],
            self.db.VehicleRecord.speed.isnot(None)
        )

        results = []
        for record in query.order_by(self.db.VehicleRecord.speed.desc()).limit(50):
            results.append({
                'type': 'vehicle',
                'vehicle_type': record.vehicle_type,
                'color': record.color,
                'speed': record.speed,
                'timestamp': record.timestamp.isoformat()
            })

        session.close()
        return results

    def _query_vehicle_by_color(self, entities: Dict, time_range: Dict) -> List[Dict]:
        """Query vehicles by color"""
        if not self.db:
            return []

        color = entities.get('color')
        if not color:
            return self._query_vehicle_detections(entities, time_range)

        session = self.db.Session()
        query = session.query(self.db.VehicleRecord).filter(
            self.db.VehicleRecord.timestamp >= time_range['start'],
            self.db.VehicleRecord.timestamp <= time_range['end'],
            self.db.VehicleRecord.color.like(f'%{color}%')
        )

        results = []
        for record in query.order_by(self.db.VehicleRecord.timestamp.desc()).limit(50):
            results.append({
                'type': 'vehicle',
                'vehicle_type': record.vehicle_type,
                'color': record.color,
                'speed': record.speed,
                'timestamp': record.timestamp.isoformat()
            })

        session.close()
        return results

    def _query_pet_detections(self, entities: Dict, time_range: Dict) -> List[Dict]:
        """Query pet detections (dogs, cats)"""
        if not self.db:
            return []

        session = self.db.Session()
        query = session.query(self.db.Detection).filter(
            self.db.Detection.timestamp >= time_range['start'],
            self.db.Detection.timestamp <= time_range['end'],
            self.db.Detection.object_type.in_(['dog', 'cat'])
        )

        results = []
        for record in query.order_by(self.db.Detection.timestamp.desc()).limit(50):
            results.append({
                'type': 'pet',
                'pet_type': record.object_type,
                'timestamp': record.timestamp.isoformat(),
                'confidence': record.confidence
            })

        session.close()
        return results

    def _query_motion_events(self, time_range: Dict) -> List[Dict]:
        """Query motion events"""
        if not self.db:
            return []

        session = self.db.Session()
        query = session.query(self.db.ActivityLog).filter(
            self.db.ActivityLog.timestamp >= time_range['start'],
            self.db.ActivityLog.timestamp <= time_range['end'],
            self.db.ActivityLog.activity_type == 'motion'
        )

        results = []
        for record in query.order_by(self.db.ActivityLog.timestamp.desc()).limit(50):
            results.append({
                'type': 'motion',
                'timestamp': record.timestamp.isoformat(),
                'details': record.details
            })

        session.close()
        return results

    def _query_anomalies(self, time_range: Dict) -> List[Dict]:
        """Query anomalies and unusual events"""
        if not self.db:
            return []

        session = self.db.Session()
        query = session.query(self.db.Anomaly).filter(
            self.db.Anomaly.timestamp >= time_range['start'],
            self.db.Anomaly.timestamp <= time_range['end']
        )

        results = []
        for record in query.order_by(self.db.Anomaly.timestamp.desc()).limit(50):
            results.append({
                'type': 'anomaly',
                'anomaly_type': record.anomaly_type,
                'severity': record.severity,
                'description': record.description,
                'timestamp': record.timestamp.isoformat(),
                'resolved': record.resolved
            })

        session.close()
        return results

    def _query_recordings(self, time_range: Dict) -> List[Dict]:
        """Query video recordings"""
        import os

        recordings_dir = self.config.get('recording.recordings_path', './recordings')
        if not os.path.exists(recordings_dir):
            return []

        results = []
        for filename in os.listdir(recordings_dir):
            if not filename.endswith(('.mp4', '.avi')):
                continue

            filepath = os.path.join(recordings_dir, filename)
            stat = os.stat(filepath)
            created_time = datetime.fromtimestamp(stat.st_ctime)

            # Filter by time range
            if time_range['start'] <= created_time <= time_range['end']:
                results.append({
                    'type': 'recording',
                    'filename': filename,
                    'filepath': filepath,
                    'timestamp': created_time.isoformat(),
                    'size': stat.st_size
                })

        # Sort by time, newest first
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        return results[:50]

    def _query_license_plates(self, entities: Dict, time_range: Dict) -> List[Dict]:
        """Query license plate detections"""
        if not self.db:
            return []

        plate_number = entities.get('plate_number')

        session = self.db.Session()
        query = session.query(self.db.LicensePlate).filter(
            self.db.LicensePlate.timestamp >= time_range['start'],
            self.db.LicensePlate.timestamp <= time_range['end']
        )

        # Filter by specific plate if provided
        if plate_number:
            query = query.filter(self.db.LicensePlate.plate_number.like(f'%{plate_number}%'))

        results = []
        for record in query.order_by(self.db.LicensePlate.timestamp.desc()).limit(50):
            results.append({
                'type': 'license_plate',
                'plate_number': record.plate_number,
                'confidence': record.confidence,
                'vehicle_type': record.vehicle_type,
                'vehicle_color': record.vehicle_color,
                'timestamp': record.timestamp.isoformat()
            })

        session.close()
        return results

    def _query_all_detections(self, entities: Dict, time_range: Dict) -> List[Dict]:
        """Query all detections"""
        if not self.db:
            return []

        session = self.db.Session()
        query = session.query(self.db.Detection).filter(
            self.db.Detection.timestamp >= time_range['start'],
            self.db.Detection.timestamp <= time_range['end']
        )

        # Filter by object type if specified
        if 'object_type' in entities:
            obj_type = entities['object_type']
            if obj_type == 'vehicle':
                query = query.filter(self.db.Detection.object_type.in_(['car', 'truck', 'bus', 'motorcycle']))
            elif obj_type == 'pet':
                query = query.filter(self.db.Detection.object_type.in_(['dog', 'cat']))
            else:
                query = query.filter(self.db.Detection.object_type == obj_type)

        results = []
        for record in query.order_by(self.db.Detection.timestamp.desc()).limit(50):
            results.append({
                'type': 'detection',
                'object_type': record.object_type,
                'timestamp': record.timestamp.isoformat(),
                'confidence': record.confidence
            })

        session.close()
        return results

    def _format_response(self, intent: str, entities: Dict, results: List[Dict], time_range: Dict) -> str:
        """Format human-readable response"""
        if not results:
            return self._format_no_results_response(intent, entities, time_range)

        count = len(results)

        # Format based on intent
        if intent in ['person_detection', 'named_person']:
            return self._format_person_response(results, entities, count)

        elif intent == 'vehicle_detection':
            return self._format_vehicle_response(results, count)

        elif intent == 'vehicle_speed':
            return self._format_speed_response(results, count)

        elif intent == 'vehicle_color':
            return self._format_color_response(results, entities, count)

        elif intent == 'anomaly':
            return self._format_anomaly_response(results, count)

        elif intent == 'recordings':
            return self._format_recording_response(results, count)

        elif intent in ['license_plate', 'specific_plate']:
            return self._format_plate_response(results, entities, count)

        else:
            return f"Found {count} detection(s) matching your query."

    def _format_person_response(self, results: List[Dict], entities: Dict, count: int) -> str:
        """Format person detection response"""
        person_name = entities.get('person_name')

        if person_name:
            recognized = [r for r in results if r.get('is_recognized')]
            if recognized:
                latest = recognized[0]
                return f"Found {len(recognized)} appearance(s) of {person_name}. Most recent: {self._format_time(latest['timestamp'])}"
            return f"No appearances of {person_name} found in the specified time range."

        # Group by name
        by_name = {}
        for r in results:
            name = r.get('name', 'Unknown')
            by_name[name] = by_name.get(name, 0) + 1

        summary = ", ".join([f"{name} ({count}x)" for name, count in by_name.items()])
        return f"Found {count} person detection(s): {summary}"

    def _format_vehicle_response(self, results: List[Dict], count: int) -> str:
        """Format vehicle detection response"""
        latest = results[0]
        response = f"Found {count} vehicle(s). "

        if latest.get('color'):
            response += f"Most recent: {latest['color']} {latest['vehicle_type']} at {self._format_time(latest['timestamp'])}"
        else:
            response += f"Most recent: {latest['vehicle_type']} at {self._format_time(latest['timestamp'])}"

        if latest.get('speed'):
            response += f" (speed: {latest['speed']:.1f} km/h)"

        return response

    def _format_speed_response(self, results: List[Dict], count: int) -> str:
        """Format speed query response"""
        fastest = results[0]  # Already sorted by speed desc
        avg_speed = sum(r['speed'] for r in results) / len(results)

        return f"Found {count} vehicle(s) with speed data. Fastest: {fastest['speed']:.1f} km/h. Average: {avg_speed:.1f} km/h"

    def _format_color_response(self, results: List[Dict], entities: Dict, count: int) -> str:
        """Format color query response"""
        color = entities.get('color', 'specified')
        latest = results[0]

        return f"Found {count} {color} vehicle(s). Most recent at {self._format_time(latest['timestamp'])}"

    def _format_anomaly_response(self, results: List[Dict], count: int) -> str:
        """Format anomaly query response"""
        unresolved = [r for r in results if not r.get('resolved')]

        if unresolved:
            latest = unresolved[0]
            return f"Found {len(unresolved)} unresolved anomaly/anomalies. Latest: {latest['description']} at {self._format_time(latest['timestamp'])}"

        return f"Found {count} anomaly/anomalies (all resolved)."

    def _format_recording_response(self, results: List[Dict], count: int) -> str:
        """Format recording query response"""
        return f"Found {count} recording(s) matching your criteria."

    def _format_plate_response(self, results: List[Dict], entities: Dict, count: int) -> str:
        """Format license plate query response"""
        plate_number = entities.get('plate_number')

        if plate_number:
            return f"Found {count} occurrence(s) of license plate {plate_number}."

        # Count unique plates
        unique_plates = len(set(r['plate_number'] for r in results))
        latest = results[0]

        return f"Found {count} license plate detection(s) ({unique_plates} unique plates). Most recent: {latest['plate_number']} at {self._format_time(latest['timestamp'])}"

    def _format_no_results_response(self, intent: str, entities: Dict, time_range: Dict) -> str:
        """Format response when no results found"""
        time_str = self._format_time_range(time_range)

        if intent in ['person_detection', 'named_person']:
            person_name = entities.get('person_name')
            if person_name:
                return f"No detections of {person_name} found {time_str}."
            return f"No person detections found {time_str}."

        elif intent == 'vehicle_detection':
            return f"No vehicles detected {time_str}."

        elif intent == 'anomaly':
            return f"No anomalies detected {time_str}. Everything looks normal!"

        elif intent in ['license_plate', 'specific_plate']:
            plate_number = entities.get('plate_number')
            if plate_number:
                return f"No detections of license plate {plate_number} found {time_str}."
            return f"No license plates detected {time_str}."

        return f"No results found {time_str}."

    def _format_time(self, timestamp_str: str) -> str:
        """Format timestamp for display"""
        try:
            dt = datetime.fromisoformat(timestamp_str)
            now = datetime.now()
            diff = now - dt

            if diff.total_seconds() < 60:
                return "just now"
            elif diff.total_seconds() < 3600:
                mins = int(diff.total_seconds() / 60)
                return f"{mins} minute(s) ago"
            elif diff.total_seconds() < 86400:
                hours = int(diff.total_seconds() / 3600)
                return f"{hours} hour(s) ago"
            else:
                return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return timestamp_str

    def _format_time_range(self, time_range: Dict) -> str:
        """Format time range for display"""
        start = time_range['start']
        now = datetime.now()
        diff = now - start

        if diff.total_seconds() < 3600:
            return "in the last hour"
        elif diff.total_seconds() < 86400:
            return "today"
        elif diff.total_seconds() < 172800:
            return "in the last 24 hours"
        else:
            days = int(diff.total_seconds() / 86400)
            return f"in the last {days} days"


class ChatbotConversationManager:
    """Manages chatbot conversation history and context"""

    def __init__(self):
        """Initialize conversation manager"""
        self.conversations = {}  # session_id -> conversation history
        self.max_history = 50

    def add_message(self, session_id: str, role: str, content: str, metadata: Dict = None):
        """Add message to conversation history"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        message = {
            'role': role,  # 'user' or 'assistant'
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }

        self.conversations[session_id].append(message)

        # Trim history if too long
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]

    def get_conversation(self, session_id: str) -> List[Dict]:
        """Get conversation history for session"""
        return self.conversations.get(session_id, [])

    def clear_conversation(self, session_id: str):
        """Clear conversation history"""
        if session_id in self.conversations:
            del self.conversations[session_id]
