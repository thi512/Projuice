"""
Web interface for camera monitoring
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

# Global reference to camera system (will be set by main app)
camera_system = None


def init_web_server(cam_system):
    """Initialize web server with camera system reference"""
    global camera_system
    camera_system = cam_system


@app.route('/')
def index():
    """Render main dashboard"""
    return render_template('index.html')


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
        'uptime': str(datetime.now() - camera_system.start_time) if hasattr(camera_system, 'start_time') else 'N/A'
    })


@app.route('/api/stats')
def get_stats():
    """Get detection statistics"""
    if camera_system is None:
        return jsonify({'error': 'Camera system not initialized'}), 500

    return jsonify(camera_system.get_stats())


@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """Get or update configuration"""
    if camera_system is None:
        return jsonify({'error': 'Camera system not initialized'}), 500

    if request.method == 'GET':
        return jsonify(camera_system.config.config)

    elif request.method == 'POST':
        new_config = request.json
        # Update config (simplified - in production, validate first)
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


@app.route('/api/snapshots')
def get_snapshots():
    """Get list of snapshot images"""
    snapshots_dir = os.path.join(
        camera_system.config.get('recording.recordings_path', './recordings'),
        'snapshots'
    )

    if not os.path.exists(snapshots_dir):
        return jsonify([])

    snapshots = []
    for filename in os.listdir(snapshots_dir):
        if filename.endswith('.jpg'):
            filepath = os.path.join(snapshots_dir, filename)
            stat = os.stat(filepath)
            snapshots.append({
                'filename': filename,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'path': filepath
            })

    snapshots.sort(key=lambda x: x['created'], reverse=True)
    return jsonify(snapshots[:20])  # Return latest 20


def generate_frames():
    """Generate frames for video streaming"""
    while True:
        if camera_system is None or not camera_system.is_running:
            break

        frame = camera_system.get_display_frame()
        if frame is None:
            continue

        # Encode frame as JPEG
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


def run_server(host='0.0.0.0', port=5000):
    """Run the web server"""
    logger.info(f"Starting web server on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
