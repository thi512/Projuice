#!/usr/bin/env python3
"""
Installation verification script for Home AI Camera System
"""
import sys

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major >= 3 and version.minor >= 8:
        print("✓ Python version OK")
        return True
    else:
        print("✗ Python 3.8+ required")
        return False

def check_opencv():
    """Check OpenCV installation"""
    try:
        import cv2
        print(f"OpenCV version: {cv2.__version__}")
        print("✓ OpenCV installed")
        return True
    except ImportError:
        print("✗ OpenCV not installed")
        print("  Install with: pip install opencv-python")
        return False

def check_ultralytics():
    """Check Ultralytics YOLO installation"""
    try:
        from ultralytics import YOLO
        print("✓ Ultralytics YOLO installed")
        return True
    except ImportError:
        print("✗ Ultralytics not installed")
        print("  Install with: pip install ultralytics")
        return False

def check_flask():
    """Check Flask installation"""
    try:
        import flask
        print(f"Flask version: {flask.__version__}")
        print("✓ Flask installed")
        return True
    except ImportError:
        print("✗ Flask not installed")
        print("  Install with: pip install flask")
        return False

def check_numpy():
    """Check NumPy installation"""
    try:
        import numpy as np
        print(f"NumPy version: {np.__version__}")
        print("✓ NumPy installed")
        return True
    except ImportError:
        print("✗ NumPy not installed")
        return False

def check_camera():
    """Check camera accessibility"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret:
                print("✓ Camera accessible and working")
                return True
            else:
                print("⚠ Camera detected but cannot read frames")
                return False
        else:
            print("✗ Cannot open camera")
            print("  Check camera connection and permissions")
            return False
    except Exception as e:
        print(f"✗ Error accessing camera: {e}")
        return False

def check_gpu():
    """Check GPU availability"""
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✓ CUDA available - GPU: {torch.cuda.get_device_name(0)}")
            return True
        else:
            print("ℹ CUDA not available (CPU only)")
            return False
    except ImportError:
        print("ℹ PyTorch not installed (GPU check skipped)")
        return False

def check_all_requirements():
    """Check all requirements from requirements.txt"""
    try:
        with open('requirements.txt', 'r') as f:
            requirements = [line.strip().split('==')[0] for line in f if line.strip() and not line.startswith('#')]

        missing = []
        for req in requirements:
            try:
                __import__(req.replace('-', '_'))
            except ImportError:
                missing.append(req)

        if not missing:
            print("✓ All requirements installed")
            return True
        else:
            print(f"✗ Missing packages: {', '.join(missing)}")
            return False
    except FileNotFoundError:
        print("⚠ requirements.txt not found")
        return False

def main():
    """Run all checks"""
    print("=" * 60)
    print("Home AI Camera System - Installation Verification")
    print("=" * 60)
    print()

    checks = [
        ("Python Version", check_python_version),
        ("OpenCV", check_opencv),
        ("Ultralytics YOLO", check_ultralytics),
        ("Flask", check_flask),
        ("NumPy", check_numpy),
        ("Camera", check_camera),
        ("GPU Support", check_gpu),
        ("All Requirements", check_all_requirements),
    ]

    results = []
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        print("-" * 60)
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Error during check: {e}")
            results.append((name, False))

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} - {name}")

    print()
    print(f"Results: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 All checks passed! You're ready to run the system.")
        print("   Start with: python main.py")
        return 0
    else:
        print("\n⚠ Some checks failed. Please install missing dependencies.")
        print("   Run: pip install -r requirements.txt")
        return 1

if __name__ == '__main__':
    sys.exit(main())
