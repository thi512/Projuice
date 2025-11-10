"""
Enhanced web server with advanced analytics endpoints
"""
from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit
import cv2
import logging
import json
from datetime import datetime
import os

from .chatbot_query_engine import ChatbotQueryEngine, ChatbotConversationManager
from .camera_discovery import CameraDiscovery
from .camera_manager import CameraManager
from .entity_labeling import EntityLabeling
from .ha_settings_manager import HomeAssistantSettingsManager

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SECRET_KEY'] = 'home-ai-camera-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global reference to enhanced camera system
camera_system = None
chatbot_engine = None
conversation_manager = None
camera_discovery = None
camera_manager = None
entity_labeling = None
ha_settings = None


def init_enhanced_web_server(cam_system):
    """Initialize enhanced web server with camera system reference"""
    global camera_system, chatbot_engine, conversation_manager
    global camera_discovery, camera_manager, entity_labeling, ha_settings

    camera_system = cam_system

    # Initialize chatbot components
    if hasattr(cam_system, 'db') and cam_system.db:
        chatbot_engine = ChatbotQueryEngine(cam_system.db, cam_system.config)
        conversation_manager = ChatbotConversationManager()
        logger.info("Chatbot query engine initialized")

    # Initialize new components
    camera_discovery = CameraDiscovery()
    camera_manager = CameraManager()
    entity_labeling = EntityLabeling(
        cam_system.db if hasattr(cam_system, 'db') else None,
        cam_system.face_ai if hasattr(cam_system, 'face_ai') else None
    )
    ha_settings = HomeAssistantSettingsManager()
    logger.info("Settings managers initialized")


@app.route('/')
def index():
    """Render main dashboard"""
    return render_template('index.html')


@app.route('/analytics')
def analytics():
    """Render analytics dashboard"""
    return render_template('analytics.html')


@app.route('/annotate')
def annotate():
    """Render interactive annotation interface"""
    return render_template('annotate.html')


@app.route('/chat')
def chat():
    """Render chatbot interface"""
    return render_template('chat.html')


@app.route('/api/status')
def get_status():
    """Get system status"""
    if camera_system is None:
        return jsonify({'error': 'Camera system not initialized'}), 500

    return jsonify({
        'running': camera_system.is_running,
        'recording': camera_system.is_recording,
        'detections_enabled': camera_system.config.get('detection.enable_object_detection'),
        'motion_enabled': camera_system.config.get('detection.enable_motion_detection'),
        'uptime': str(datetime.now() - camera_system.start_time) if hasattr(camera_system, 'start_time') else 'N/A',
        'ai_features_enabled': camera_system.config.get('ai_features.face_recognition.enabled', False)
    })


@app.route('/api/stats')
def get_stats():
    """Get detection statistics"""
    if camera_system is None:
        return jsonify({'error': 'Camera system not initialized'}), 500

    return jsonify(camera_system.get_stats())


@app.route('/api/analytics/comprehensive')
def get_comprehensive_analytics():
    """Get comprehensive analytics data"""
    if camera_system is None:
        return jsonify({'error': 'Camera system not initialized'}), 500

    # Gather all analytics
    analytics = {}

    # Learning status
    if hasattr(camera_system, 'learning_system'):
        analytics['learning_status'] = camera_system.learning_system.get_learning_status()
        analytics['learning_status']['next_task'] = camera_system.learning_system.suggest_next_learning_task()
        analytics['learning_status']['latest_insight'] = camera_system.get_latest_insight()

    # Hourly/daily activity
    if hasattr(camera_system, 'db'):
        analytics['hourly_activity'] = camera_system.db.get_hourly_activity(days=7)
        analytics['daily_activity'] = camera_system.db.get_daily_activity(days=30)

    # Vehicle statistics
    if hasattr(camera_system, 'db'):
        vehicle_stats = camera_system.db.get_vehicle_statistics(hours=24)
        analytics['vehicle_stats'] = vehicle_stats
        analytics['color_distribution'] = vehicle_stats.get('color_distribution', {})

    # Known people
    if hasattr(camera_system, 'face_ai'):
        analytics['known_people'] = camera_system.face_ai.get_known_people()

    # Anomalies
    if hasattr(camera_system, 'db'):
        analytics['anomalies'] = camera_system.db.get_anomalies(hours=24, unresolved_only=True)

    # Learned patterns
    analytics['patterns'] = camera_system.get_learned_patterns()

    return jsonify(analytics)


@app.route('/api/people')
def get_people():
    """Get list of known people"""
    if not hasattr(camera_system, 'face_ai'):
        return jsonify([])

    return jsonify(camera_system.face_ai.get_known_people())


@app.route('/api/people/<person_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_person(person_id):
    """Manage a specific person"""
    if not hasattr(camera_system, 'face_ai'):
        return jsonify({'error': 'Face recognition not enabled'}), 400

    if request.method == 'GET':
        # Get person history
        history = camera_system.db.get_person_history(person_id, days=30)
        profile = camera_system.behavior.get_person_profile(person_id)
        return jsonify({
            'history': history,
            'profile': profile
        })

    elif request.method == 'PUT':
        # Rename person
        data = request.json
        new_name = data.get('name')
        if new_name:
            success = camera_system.face_ai.rename_person(person_id, new_name)
            return jsonify({'success': success})
        return jsonify({'error': 'Name required'}), 400

    elif request.method == 'DELETE':
        # Delete person
        success = camera_system.face_ai.delete_person(person_id)
        return jsonify({'success': success})


@app.route('/api/anomalies')
def get_anomalies():
    """Get anomaly records"""
    hours = request.args.get('hours', 24, type=int)
    unresolved_only = request.args.get('unresolved', 'true').lower() == 'true'

    if not hasattr(camera_system, 'db'):
        return jsonify([])

    anomalies = camera_system.db.get_anomalies(hours=hours, unresolved_only=unresolved_only)
    return jsonify(anomalies)


@app.route('/api/learning/trigger', methods=['POST'])
def trigger_learning():
    """Manually trigger learning cycle"""
    if not hasattr(camera_system, 'learning_system'):
        return jsonify({'error': 'Learning system not enabled'}), 400

    camera_system.learning_system.force_learning_cycle()
    return jsonify({'success': True, 'message': 'Learning cycle triggered'})


@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """Get or update configuration"""
    if camera_system is None:
        return jsonify({'error': 'Camera system not initialized'}), 500

    if request.method == 'GET':
        return jsonify(camera_system.config.config)

    elif request.method == 'POST':
        new_config = request.json
        for key, value in new_config.items():
            camera_system.config.set(key, value)
        camera_system.config.save()
        return jsonify({'status': 'success'})


@app.route('/api/recordings')
def get_recordings():
    """Get list of recorded videos"""
    recordings_dir = camera_system.config.get('recording.recordings_path', './recordings')

    if not os.path.exists(recordings_dir):
        return jsonify([])

    videos = []
    for filename in os.listdir(recordings_dir):
        if filename.endswith(('.mp4', '.avi')):
            filepath = os.path.join(recordings_dir, filename)
            stat = os.stat(filepath)
            videos.append({
                'filename': filename,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'path': filepath
            })

    videos.sort(key=lambda x: x['created'], reverse=True)
    return jsonify(videos)


@app.route('/api/annotations/add', methods=['POST'])
def add_annotation():
    """Add user annotation for interactive learning"""
    if not hasattr(camera_system, 'interactive_learning'):
        return jsonify({'success': False, 'message': 'Interactive learning not enabled'}), 400

    data = request.json
    bbox = data.get('bbox')  # [x1, y1, x2, y2]
    class_name = data.get('class_name')
    description = data.get('description', '')

    if not bbox or not class_name:
        return jsonify({'success': False, 'message': 'Missing bbox or class_name'}), 400

    # Get current frame
    frame = camera_system.get_display_frame()
    if frame is None:
        return jsonify({'success': False, 'message': 'No frame available'}), 400

    try:
        # Add annotation
        anno_id = camera_system.interactive_learning.add_annotation(
            frame=frame,
            bbox=tuple(map(int, bbox)),
            class_name=class_name,
            description=description
        )

        return jsonify({
            'success': True,
            'annotation_id': anno_id,
            'message': 'Annotation added successfully'
        })
    except Exception as e:
        logger.error(f"Failed to add annotation: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/annotations/stats')
def get_annotation_stats():
    """Get annotation statistics"""
    if not hasattr(camera_system, 'interactive_learning'):
        return jsonify({'total_annotations': 0, 'pending_annotations': 0})

    stats = camera_system.interactive_learning.get_statistics()
    return jsonify(stats)


@app.route('/api/annotations/recent')
def get_recent_annotations():
    """Get recent annotations"""
    if not hasattr(camera_system, 'interactive_learning'):
        return jsonify([])

    limit = request.args.get('limit', 20, type=int)
    annotations = camera_system.interactive_learning.get_recent_annotations(limit)
    return jsonify(annotations)


@app.route('/api/annotations/<annotation_id>', methods=['DELETE'])
def delete_annotation(annotation_id):
    """Delete an annotation"""
    if not hasattr(camera_system, 'interactive_learning'):
        return jsonify({'success': False, 'message': 'Interactive learning not enabled'}), 400

    success = camera_system.interactive_learning.delete_annotation(annotation_id)
    return jsonify({'success': success})


@app.route('/api/annotations/train', methods=['POST'])
def trigger_training():
    """Trigger model training with user annotations"""
    if not hasattr(camera_system, 'interactive_learning'):
        return jsonify({'success': False, 'message': 'Interactive learning not enabled'}), 400

    data = request.json or {}
    epochs = data.get('epochs', 10)
    batch_size = data.get('batch_size', 16)

    try:
        result = camera_system.interactive_learning.trigger_training(
            epochs=epochs,
            batch_size=batch_size
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/annotations/text', methods=['POST'])
def add_text_annotation():
    """Add annotation from text description"""
    if not hasattr(camera_system, 'interactive_learning'):
        return jsonify({'success': False, 'message': 'Interactive learning not enabled'}), 400

    data = request.json
    description = data.get('description')
    bbox = data.get('bbox')  # Optional

    if not description:
        return jsonify({'success': False, 'message': 'Description required'}), 400

    frame = camera_system.get_display_frame()
    if frame is None:
        return jsonify({'success': False, 'message': 'No frame available'}), 400

    try:
        if bbox:
            bbox = tuple(map(int, bbox))

        anno_id = camera_system.interactive_learning.add_text_description(
            text_description=description,
            frame=frame,
            bbox=bbox
        )

        return jsonify({
            'success': True,
            'annotation_id': anno_id,
            'message': 'Text annotation added successfully'
        })
    except Exception as e:
        logger.error(f"Failed to add text annotation: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/chat/query', methods=['POST'])
def chat_query():
    """Process chatbot query"""
    if not chatbot_engine:
        return jsonify({'success': False, 'message': 'Chatbot not initialized'}), 400

    data = request.json
    query = data.get('query')
    session_id = data.get('session_id', 'default')

    if not query:
        return jsonify({'success': False, 'message': 'Query required'}), 400

    try:
        # Process query
        result = chatbot_engine.process_query(query)

        # Save to conversation history
        if conversation_manager:
            conversation_manager.add_message(session_id, 'user', query)
            conversation_manager.add_message(
                session_id,
                'assistant',
                result['response'],
                metadata={'intent': result['intent'], 'result_count': len(result['results'])}
            )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Chat query failed: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/chat/history/<session_id>')
def get_chat_history(session_id):
    """Get conversation history for session"""
    if not conversation_manager:
        return jsonify([])

    history = conversation_manager.get_conversation(session_id)
    return jsonify(history)


@app.route('/api/chat/clear/<session_id>', methods=['POST'])
def clear_chat_history(session_id):
    """Clear conversation history"""
    if conversation_manager:
        conversation_manager.clear_conversation(session_id)

    return jsonify({'success': True})


@app.route('/settings')
def settings_page():
    """Render settings page"""
    return render_template('settings.html')


@app.route('/api/speed/settings', methods=['GET'])
def get_speed_settings():
    """Get current speed calibration settings"""
    if not hasattr(camera_system, 'speed_estimator'):
        return jsonify({'error': 'Speed estimator not available'}), 500

    return jsonify(camera_system.speed_estimator.get_settings())


@app.route('/api/speed/settings', methods=['POST'])
def update_speed_settings():
    """Update speed calibration settings"""
    if not hasattr(camera_system, 'speed_estimator'):
        return jsonify({'error': 'Speed estimator not available'}), 500

    try:
        settings = request.json
        success = camera_system.speed_estimator.update_settings(settings)

        if success:
            return jsonify({
                'success': True,
                'message': 'Settings updated successfully',
                'settings': camera_system.speed_estimator.get_settings()
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to save settings'}), 500

    except Exception as e:
        logger.error(f"Failed to update speed settings: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/speed/calibration/guide', methods=['GET'])
def get_calibration_guide():
    """Get calibration guide for current method"""
    if not hasattr(camera_system, 'speed_estimator'):
        return jsonify({'error': 'Speed estimator not available'}), 500

    return jsonify(camera_system.speed_estimator.get_calibration_guide())


@app.route('/api/speed/statistics', methods=['GET'])
def get_speed_statistics():
    """Get speed measurement statistics"""
    if not hasattr(camera_system, 'speed_estimator'):
        return jsonify({'error': 'Speed estimator not available'}), 500

    return jsonify(camera_system.speed_estimator.get_speed_statistics())


@app.route('/api/speed/clear', methods=['POST'])
def clear_speed_tracking():
    """Clear speed tracking data"""
    if not hasattr(camera_system, 'speed_estimator'):
        return jsonify({'error': 'Speed estimator not available'}), 500

    camera_system.speed_estimator.clear_tracking()
    return jsonify({'success': True, 'message': 'Tracking data cleared'})


# ===== Camera Management API =====

@app.route('/api/cameras/discover', methods=['POST'])
def discover_cameras():
    """Discover cameras on the network"""
    if not camera_discovery:
        return jsonify({'error': 'Camera discovery not available'}), 500

    try:
        data = request.json or {}
        network_range = data.get('network_range')

        cameras = camera_discovery.discover_all(network_range)
        return jsonify({'success': True, 'cameras': cameras, 'count': len(cameras)})

    except Exception as e:
        logger.error(f"Camera discovery failed: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/cameras/discover/nvr', methods=['POST'])
def discover_nvr_cameras():
    """Discover all cameras connected to an NVR"""
    if not camera_discovery:
        return jsonify({'error': 'Camera discovery not available'}), 500

    try:
        data = request.json or {}
        nvr_ip = data.get('nvr_ip')
        nvr_port = data.get('nvr_port', 80)
        username = data.get('username', '')
        password = data.get('password', '')
        nvr_type = data.get('nvr_type', 'auto')

        if not nvr_ip:
            return jsonify({'success': False, 'message': 'NVR IP required'}), 400

        cameras = camera_discovery.discover_nvr_cameras(
            nvr_ip, nvr_port, username, password, nvr_type
        )

        return jsonify({
            'success': True,
            'cameras': cameras,
            'count': len(cameras),
            'nvr_ip': nvr_ip,
            'nvr_type': nvr_type if nvr_type != 'auto' else 'detected'
        })

    except Exception as e:
        logger.error(f"NVR discovery failed: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/cameras/interfaces', methods=['GET'])
def get_network_interfaces():
    """Get network interfaces for scanning"""
    if not camera_discovery:
        return jsonify({'error': 'Camera discovery not available'}), 500

    interfaces = camera_discovery.get_network_interfaces()
    return jsonify({'interfaces': interfaces})


@app.route('/api/cameras', methods=['GET'])
def get_cameras():
    """Get all cameras"""
    if not camera_manager:
        return jsonify({'error': 'Camera manager not available'}), 500

    cameras = camera_manager.get_all_cameras()
    return jsonify({'cameras': cameras})


@app.route('/api/cameras', methods=['POST'])
def add_camera():
    """Add a new camera"""
    if not camera_manager:
        return jsonify({'error': 'Camera manager not available'}), 500

    try:
        camera = request.json
        camera_id = camera_manager.add_camera(camera)
        return jsonify({'success': True, 'camera_id': camera_id})

    except Exception as e:
        logger.error(f"Failed to add camera: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/cameras/<camera_id>', methods=['PUT'])
def update_camera(camera_id):
    """Update camera settings"""
    if not camera_manager:
        return jsonify({'error': 'Camera manager not available'}), 500

    try:
        updates = request.json
        success = camera_manager.update_camera(camera_id, updates)
        return jsonify({'success': success})

    except Exception as e:
        logger.error(f"Failed to update camera: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/cameras/<camera_id>', methods=['DELETE'])
def delete_camera(camera_id):
    """Delete a camera"""
    if not camera_manager:
        return jsonify({'error': 'Camera manager not available'}), 500

    try:
        success = camera_manager.remove_camera(camera_id)
        return jsonify({'success': success})

    except Exception as e:
        logger.error(f"Failed to delete camera: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/cameras/homepage', methods=['GET'])
def get_homepage_cameras():
    """Get cameras for homepage"""
    if not camera_manager:
        return jsonify({'error': 'Camera manager not available'}), 500

    cameras = camera_manager.get_homepage_cameras()
    camera_ids = camera_manager.homepage_cameras
    return jsonify({'cameras': cameras, 'camera_ids': camera_ids})


@app.route('/api/cameras/homepage', methods=['POST'])
def set_homepage_cameras():
    """Set cameras for homepage"""
    if not camera_manager:
        return jsonify({'error': 'Camera manager not available'}), 500

    try:
        data = request.json
        camera_ids = data.get('camera_ids', [])
        camera_manager.set_homepage_cameras(camera_ids)
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Failed to set homepage cameras: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/cameras/<camera_id>/test', methods=['POST'])
def test_camera_connection(camera_id):
    """Test camera connection"""
    if not camera_manager:
        return jsonify({'error': 'Camera manager not available'}), 500

    try:
        camera = camera_manager.get_camera(camera_id)
        if not camera:
            return jsonify({'success': False, 'message': 'Camera not found'}), 404

        data = request.json or {}
        username = data.get('username', '')
        password = data.get('password', '')

        result = camera_manager.test_camera_connection(camera, username, password)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Camera test failed: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ===== Entity Labeling API =====

@app.route('/api/entities/unlabeled/faces', methods=['GET'])
def get_unlabeled_faces():
    """Get unlabeled faces"""
    if not entity_labeling:
        return jsonify({'error': 'Entity labeling not available'}), 500

    min_appearances = request.args.get('min_appearances', 3, type=int)
    days = request.args.get('days', 30, type=int)

    faces = entity_labeling.get_unlabeled_faces(min_appearances, days)
    return jsonify({'faces': faces})


@app.route('/api/entities/unlabeled/vehicles', methods=['GET'])
def get_unlabeled_vehicles():
    """Get frequent vehicles"""
    if not entity_labeling:
        return jsonify({'error': 'Entity labeling not available'}), 500

    min_appearances = request.args.get('min_appearances', 5, type=int)
    days = request.args.get('days', 30, type=int)

    vehicles = entity_labeling.get_frequent_vehicles(min_appearances, days)
    return jsonify({'vehicles': vehicles})


@app.route('/api/entities/label/face', methods=['POST'])
def label_face():
    """Label a face"""
    if not entity_labeling:
        return jsonify({'error': 'Entity labeling not available'}), 500

    try:
        data = request.json
        person_id = data.get('person_id')
        new_name = data.get('name')
        notes = data.get('notes', '')

        success = entity_labeling.label_face(person_id, new_name, notes)
        return jsonify({'success': success})

    except Exception as e:
        logger.error(f"Failed to label face: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/entities/label/vehicle', methods=['POST'])
def label_vehicle():
    """Label a vehicle"""
    if not entity_labeling:
        return jsonify({'error': 'Entity labeling not available'}), 500

    try:
        data = request.json
        identifier = data.get('identifier')
        label = data.get('label')
        notes = data.get('notes', '')

        success = entity_labeling.label_vehicle(identifier, label, notes)
        return jsonify({'success': success})

    except Exception as e:
        logger.error(f"Failed to label vehicle: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/entities/labeled', methods=['GET'])
def get_labeled_entities():
    """Get all labeled entities"""
    if not entity_labeling:
        return jsonify({'error': 'Entity labeling not available'}), 500

    entity_type = request.args.get('type', 'all')
    entities = entity_labeling.get_labeled_entities(entity_type)
    return jsonify({'entities': entities})


@app.route('/api/entities/<entity_type>/<identifier>', methods=['DELETE'])
def remove_entity_label(entity_type, identifier):
    """Remove entity label"""
    if not entity_labeling:
        return jsonify({'error': 'Entity labeling not available'}), 500

    try:
        success = entity_labeling.remove_label(identifier, entity_type)
        return jsonify({'success': success})

    except Exception as e:
        logger.error(f"Failed to remove label: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/entities/<entity_type>/<identifier>/history', methods=['GET'])
def get_entity_history(entity_type, identifier):
    """Get entity appearance history"""
    if not entity_labeling:
        return jsonify({'error': 'Entity labeling not available'}), 500

    days = request.args.get('days', 30, type=int)
    history = entity_labeling.get_entity_history(identifier, entity_type, days)
    return jsonify({'history': history})


# ===== Home Assistant Settings API =====

@app.route('/api/ha/settings', methods=['GET'])
def get_ha_settings():
    """Get Home Assistant settings"""
    if not ha_settings:
        return jsonify({'error': 'HA settings not available'}), 500

    return jsonify(ha_settings.get_settings())


@app.route('/api/ha/settings', methods=['POST'])
def update_ha_settings():
    """Update Home Assistant settings"""
    if not ha_settings:
        return jsonify({'error': 'HA settings not available'}), 500

    try:
        updates = request.json
        success = ha_settings.update_settings(updates)
        return jsonify({'success': success})

    except Exception as e:
        logger.error(f"Failed to update HA settings: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/ha/test', methods=['POST'])
def test_ha_connection():
    """Test Home Assistant MQTT connection"""
    if not ha_settings:
        return jsonify({'error': 'HA settings not available'}), 500

    result = ha_settings.test_connection()
    return jsonify(result)


@app.route('/api/ha/entities', methods=['GET'])
def get_ha_entities():
    """Get Home Assistant entity configurations"""
    if not ha_settings:
        return jsonify({'error': 'HA settings not available'}), 500

    entities = ha_settings.get_entity_configurations()
    return jsonify({'entities': entities})


@app.route('/api/ha/export', methods=['GET'])
def export_ha_config():
    """Export Home Assistant configuration"""
    if not ha_settings:
        return jsonify({'error': 'HA settings not available'}), 500

    config = ha_settings.export_config()
    return jsonify({'config': config})


def generate_frames():
    """Generate frames for video streaming"""
    while True:
        if camera_system is None or not camera_system.is_running:
            break

        frame = camera_system.get_display_frame()
        if frame is None:
            continue

        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('status', {'connected': True})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')


@socketio.on('start_recording')
def handle_start_recording():
    """Start video recording"""
    if camera_system:
        success = camera_system.start_recording()
        emit('recording_status', {'recording': success})


@socketio.on('stop_recording')
def handle_stop_recording():
    """Stop video recording"""
    if camera_system:
        camera_system.stop_recording()
        emit('recording_status', {'recording': False})


@socketio.on('take_snapshot')
def handle_snapshot():
    """Take a snapshot"""
    if camera_system:
        filepath = camera_system.take_snapshot()
        emit('snapshot_taken', {'filepath': filepath})


def run_enhanced_server(host='0.0.0.0', port=5000):
    """Run the enhanced web server"""
    logger.info(f"Starting enhanced web server on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
