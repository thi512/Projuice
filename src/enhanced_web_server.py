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

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SECRET_KEY'] = 'home-ai-camera-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global reference to enhanced camera system
camera_system = None


def init_enhanced_web_server(cam_system):
    """Initialize enhanced web server with camera system reference"""
    global camera_system
    camera_system = cam_system


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
