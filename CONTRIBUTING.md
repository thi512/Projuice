# Contributing to Home AI Camera System

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version)
   - Error messages/logs

### Suggesting Features

1. Check if the feature has been suggested
2. Create an issue describing:
   - Use case and motivation
   - Proposed implementation (if applicable)
   - Potential challenges

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the code style (PEP 8)
   - Add docstrings to functions
   - Include type hints where appropriate
   - Add unit tests if applicable

4. **Test your changes**
   ```bash
   python -m pytest tests/
   ```

5. **Commit with clear messages**
   ```bash
   git commit -m "Add feature: description"
   ```

6. **Push and create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable names
- Add comments for complex logic
- Keep functions focused and small

Example:
```python
def detect_objects(frame: np.ndarray, confidence: float = 0.5) -> List[Dict]:
    """
    Detect objects in the given frame.

    Args:
        frame: Input image frame
        confidence: Minimum confidence threshold

    Returns:
        List of detection dictionaries
    """
    # Implementation
    pass
```

## Testing

Add tests for new features:

```python
# tests/test_detector.py
def test_object_detection():
    detector = ObjectDetector()
    frame = cv2.imread('test_image.jpg')
    detections = detector.detect(frame)
    assert len(detections) > 0
```

## Documentation

- Update README.md if adding features
- Add docstrings to new functions/classes
- Update INSTALL.md for new dependencies

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
