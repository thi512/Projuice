#!/usr/bin/env python3
"""
Main entry point for Home AI and ML Camera System
"""
import argparse
import logging
import signal
import sys
from threading import Thread

from src.camera_system import CameraSystem
from src.web_server import init_web_server, run_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('camera_system.log')
    ]
)

logger = logging.getLogger(__name__)

# Global camera system instance
camera_system = None


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Shutdown signal received")
    if camera_system:
        camera_system.stop()
    sys.exit(0)


def main():
    """Main application entry point"""
    global camera_system

    parser = argparse.ArgumentParser(
        description='Home AI and ML Camera System'
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--no-web',
        action='store_true',
        help='Disable web interface'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run without display (no OpenCV window)'
    )
    parser.add_argument(
        '--record',
        action='store_true',
        help='Start recording immediately'
    )

    args = parser.parse_args()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=" * 60)
    logger.info("Home AI and ML Camera System Starting")
    logger.info("=" * 60)

    try:
        # Initialize camera system
        camera_system = CameraSystem(config_file=args.config)

        # Start camera system
        if not camera_system.start():
            logger.error("Failed to start camera system")
            return 1

        # Start recording if requested
        if args.record:
            camera_system.start_recording()

        # Start web server if enabled
        web_thread = None
        if not args.no_web:
            init_web_server(camera_system)
            web_config = camera_system.config.get_web_config()

            web_thread = Thread(
                target=run_server,
                kwargs={
                    'host': web_config['host'],
                    'port': web_config['port']
                },
                daemon=True
            )
            web_thread.start()

            logger.info(f"Web interface: http://localhost:{web_config['port']}")

        # Display window if not headless
        if not args.headless:
            logger.info("Press 'q' to quit, 'r' to toggle recording, 's' to take snapshot")

            while camera_system.is_running:
                frame = camera_system.get_display_frame()

                if frame is not None:
                    import cv2
                    cv2.imshow('Home AI Camera System', frame)

                    key = cv2.waitKey(1) & 0xFF

                    if key == ord('q'):
                        break
                    elif key == ord('r'):
                        if camera_system.is_recording:
                            filepath = camera_system.stop_recording()
                            logger.info(f"Recording stopped: {filepath}")
                        else:
                            camera_system.start_recording()
                            logger.info("Recording started")
                    elif key == ord('s'):
                        filepath = camera_system.take_snapshot()
                        logger.info(f"Snapshot saved: {filepath}")

            import cv2
            cv2.destroyAllWindows()
        else:
            # In headless mode, just keep running
            logger.info("Running in headless mode. Press Ctrl+C to stop.")
            while camera_system.is_running:
                import time
                time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    finally:
        # Cleanup
        if camera_system:
            camera_system.stop()

        logger.info("Camera system shutdown complete")

    return 0


if __name__ == '__main__':
    sys.exit(main())
