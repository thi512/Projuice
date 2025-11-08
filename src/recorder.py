"""
Video recording and storage module
"""
import cv2
import os
import logging
from datetime import datetime
from threading import Thread, Lock
from queue import Queue
import json

logger = logging.getLogger(__name__)


class VideoRecorder:
    """Handle video recording with threading"""

    def __init__(self, output_dir="recordings", codec="mp4v", fps=30):
        """
        Initialize video recorder

        Args:
            output_dir: Directory to save recordings
            codec: Video codec (mp4v, XVID, H264)
            fps: Frames per second
        """
        self.output_dir = output_dir
        self.codec = codec
        self.fps = fps
        self.is_recording = False
        self.writer = None
        self.current_filename = None
        self.frame_queue = Queue(maxsize=100)
        self.write_thread = None
        self.lock = Lock()

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

    def start_recording(self, width, height, prefix="recording"):
        """
        Start recording video

        Args:
            width: Frame width
            height: Frame height
            prefix: Filename prefix

        Returns:
            str: Path to output file
        """
        with self.lock:
            if self.is_recording:
                logger.warning("Already recording")
                return None

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}.mp4"
            filepath = os.path.join(self.output_dir, filename)

            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*self.codec)
            self.writer = cv2.VideoWriter(filepath, fourcc, self.fps, (width, height))

            if not self.writer.isOpened():
                logger.error(f"Failed to open video writer for {filepath}")
                return None

            self.current_filename = filepath
            self.is_recording = True

            # Start write thread
            self.write_thread = Thread(target=self._write_loop, daemon=True)
            self.write_thread.start()

            logger.info(f"Started recording to {filepath}")
            return filepath

    def _write_loop(self):
        """Write frames from queue to video file"""
        while self.is_recording or not self.frame_queue.empty():
            try:
                frame = self.frame_queue.get(timeout=0.1)
                if self.writer is not None:
                    self.writer.write(frame)
            except:
                continue

    def write_frame(self, frame):
        """
        Add frame to recording queue

        Args:
            frame: Frame to record
        """
        if self.is_recording:
            try:
                self.frame_queue.put_nowait(frame)
            except:
                logger.warning("Frame queue full, dropping frame")

    def stop_recording(self):
        """Stop recording and save video"""
        with self.lock:
            if not self.is_recording:
                return

            self.is_recording = False

        # Wait for write thread to finish
        if self.write_thread is not None:
            self.write_thread.join(timeout=5.0)

        # Release writer
        if self.writer is not None:
            self.writer.release()
            self.writer = None

        logger.info(f"Stopped recording: {self.current_filename}")
        saved_file = self.current_filename
        self.current_filename = None

        return saved_file

    def is_active(self):
        """Check if currently recording"""
        return self.is_recording


class EventLogger:
    """Log detection events to file"""

    def __init__(self, output_dir="recordings"):
        """
        Initialize event logger

        Args:
            output_dir: Directory to save event logs
        """
        self.output_dir = output_dir
        self.events = []
        os.makedirs(output_dir, exist_ok=True)

    def log_event(self, event_type, data=None):
        """
        Log an event

        Args:
            event_type: Type of event (motion, detection, etc.)
            data: Additional event data
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': data or {}
        }
        self.events.append(event)
        logger.info(f"Event logged: {event_type}")

    def save_events(self, filename=None):
        """
        Save events to JSON file

        Args:
            filename: Output filename (auto-generated if None)

        Returns:
            str: Path to saved file
        """
        if not self.events:
            return None

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"events_{timestamp}.json"

        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(self.events, f, indent=2)

        logger.info(f"Saved {len(self.events)} events to {filepath}")
        count = len(self.events)
        self.events = []

        return filepath, count

    def get_events(self):
        """Get all logged events"""
        return self.events

    def clear_events(self):
        """Clear all logged events"""
        self.events = []


class SnapshotManager:
    """Manage snapshot images"""

    def __init__(self, output_dir="recordings/snapshots"):
        """
        Initialize snapshot manager

        Args:
            output_dir: Directory to save snapshots
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save_snapshot(self, frame, prefix="snapshot", metadata=None):
        """
        Save a snapshot image

        Args:
            frame: Image frame to save
            prefix: Filename prefix
            metadata: Optional metadata dict to save alongside image

        Returns:
            str: Path to saved snapshot
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{prefix}_{timestamp}.jpg"
        filepath = os.path.join(self.output_dir, filename)

        # Save image
        cv2.imwrite(filepath, frame)

        # Save metadata if provided
        if metadata:
            metadata_file = filepath.replace('.jpg', '.json')
            with open(metadata_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'filename': filename,
                    **metadata
                }, f, indent=2)

        logger.info(f"Saved snapshot: {filepath}")
        return filepath

    def get_snapshots(self, limit=10):
        """
        Get recent snapshots

        Args:
            limit: Maximum number of snapshots to return

        Returns:
            list: List of snapshot filepaths
        """
        snapshots = sorted(
            [f for f in os.listdir(self.output_dir) if f.endswith('.jpg')],
            reverse=True
        )
        return [os.path.join(self.output_dir, s) for s in snapshots[:limit]]
