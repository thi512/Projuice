
# 🧠 Advanced AI Features Documentation

This document describes all the advanced AI and machine learning features of the Enhanced Home Camera System.

## Table of Contents
- [Overview](#overview)
- [Face Recognition with Learning](#face-recognition-with-learning)
- [Behavioral Analysis](#behavioral-analysis)
- [Pattern Recognition](#pattern-recognition)
- [Anomaly Detection](#anomaly-detection)
- [Vehicle Analytics](#vehicle-analytics)
- [Continuous Learning](#continuous-learning)
- [Reolink Integration](#reolink-integration)
- [Home Assistant Integration](#home-assistant-integration)
- [Database & Analytics](#database--analytics)

## Overview

The Enhanced AI Camera System includes cutting-edge machine learning capabilities that continuously learn and improve over time. The system learns what's "normal" for your environment and automatically detects unusual patterns.

### Key Capabilities
- ✅ **Self-Learning**: Automatically learns faces, patterns, and behaviors
- ✅ **Real-Time Analytics**: Speed estimation, color detection, time-based analysis
- ✅ **Anomaly Detection**: Identifies unusual activities and alerts you
- ✅ **Behavioral Profiling**: Learns when people typically appear
- ✅ **Pattern Recognition**: Discovers correlations and trends
- ✅ **Home Automation**: Integrates with Home Assistant via MQTT
- ✅ **Professional NVR Support**: Works with Reolink cameras and NVRs

## Face Recognition with Learning

### How It Works

The system uses deep learning (face_recognition library) to:
1. Detect faces in video frames
2. Generate unique encodings for each face
3. Match faces against known people
4. **Automatically learn** frequently appearing unknown faces

### Auto-Learning

**The system automatically learns new faces!**

When an unknown person appears **5 times** (configurable), the system:
- Groups similar faces together
- Creates a new person profile
- Assigns them a name like "Frequent Visitor 1"
- You can rename them later in the web interface

### Configuration

```yaml
ai_features:
  face_recognition:
    enabled: true
    tolerance: 0.6  # Lower = stricter matching (0.5-0.7 recommended)
    auto_learn_threshold: 5  # Number of appearances before auto-learning
    storage_dir: "data/faces"
```

### Features

- **Recognition Confidence**: Each detection includes a confidence score
- **Person Tracking**: Tracks when each person was first/last seen
- **Unusual Time Detection**: Alerts if person appears at unusual times
- **Manual Learning**: Add faces manually via web interface
- **Rename People**: Change names in the dashboard
- **History**: View complete appearance history per person

### API Endpoints

```
GET  /api/people                    # List all known people
GET  /api/people/{person_id}        # Get person details and history
PUT  /api/people/{person_id}        # Rename person
DELETE /api/people/{person_id}      # Delete person
```

## Behavioral Analysis

### Overview

The behavioral analysis engine learns your environment's normal patterns and detects anomalies.

### What It Learns

1. **Time Patterns**
   - Busiest hours of the day
   - Quietest times
   - Day-of-week patterns

2. **Person Behavior**
   - When each person typically appears
   - Usual paths through camera view
   - Dwell times

3. **Activity Patterns**
   - Normal activity levels by time
   - Event frequencies
   - Seasonal variations

### Anomaly Detection

Uses machine learning (Isolation Forest) to detect unusual events:

- Person appearing at unusual time
- Unexpected activity level
- Unusual movement patterns
- Abnormal vehicle speeds

### Configuration

```yaml
ai_features:
  behavioral_analysis:
    enabled: true
    learn_normal_patterns: true
    anomaly_detection: true
    min_events_for_learning: 100
```

### How Long Until It Learns?

- **100 events minimum**: Needs this many events before learning patterns
- **1 week optimal**: Best results after a week of data
- **Continuous improvement**: Gets better over time

## Pattern Recognition

### Automatic Pattern Discovery

The system continuously looks for patterns including:

### 1. Temporal Patterns
- Peak activity hours
- Quiet periods
- Day-of-week trends
- Seasonal changes

### 2. Correlation Patterns
- Activity types that occur together
- Time-based correlations
- Person-event correlations

### 3. Vehicle Patterns
- Common vehicle colors
- Average speeds
- Rush hour patterns
- Direction of travel

### Examples of Learned Patterns

The system might discover:
- "Peak activity between 7:00-9:00 AM (45 events)"
- "John Smith typically appears between 17:00-19:00"
- "Most common vehicle color: Silver (23 vehicles)"
- "Average vehicle speed: 38.5 km/h"

## Vehicle Analytics

### Speed Estimation

**Measures vehicle speed in km/h**

#### How It Works
1. Tracks vehicle position across frames
2. Calculates distance traveled (in pixels)
3. Converts to real-world speed using calibration
4. Displays speed on screen and logs to database

#### Calibration

```yaml
ai_features:
  advanced_analytics:
    speed_estimation:
      enabled: true
      pixels_per_meter: 50  # IMPORTANT: Calibrate this!
```

**To Calibrate:**
1. Measure a known distance in your camera view (e.g., 5 meters)
2. Count how many pixels that distance is in the video
3. pixels_per_meter = pixels / meters

Example: 250 pixels covers 5 meters → pixels_per_meter = 50

### Color Detection

Automatically detects and tracks vehicle colors:
- Identifies dominant color
- Tracks color distribution over time
- Beautiful pie charts in analytics dashboard

Supported colors: Red, Blue, Black, White, Silver, Gray, Green, etc.

### Time Analysis

Analyzes patterns over time:
- Hourly vehicle counts
- Daily distribution
- Peak traffic times
- Speed trends

## Continuous Learning

### Always Learning New Things

The system **never stops learning**! It continuously:

1. **Learns New Faces** (every 30 min)
   - Auto-learns frequently appearing unknowns
   - Consolidates face encodings
   - Improves recognition accuracy

2. **Updates Behavior Models** (every 1 hour)
   - Retrains anomaly detection
   - Updates normal patterns
   - Refines time-based models

3. **Discovers New Patterns** (every 2 hours)
   - Looks for correlations
   - Identifies trends
   - Suggests insights

4. **Optimizes Models** (every 6 hours)
   - Compresses data
   - Improves performance
   - Reduces storage

### Learning Schedule

```yaml
ai_features:
  continuous_learning:
    enabled: true
    face_learning_interval: 3600     # 1 hour
    pattern_learning_interval: 7200  # 2 hours
    behavior_update_interval: 1800   # 30 minutes
```

### Viewing Learning Status

Check the **Analytics Dashboard** to see:
- What the system is learning
- Latest insights discovered
- Next learning task
- Learning history

### Manual Learning Trigger

Force immediate learning:
```bash
# Via API
POST /api/learning/trigger

# Or press 'L' in GUI mode
```

## Reolink Integration

### Supported Devices

- ✅ Reolink NVR (all models)
- ✅ Standalone Reolink cameras
- ✅ Use camera's built-in AI detections

### Configuration

#### With Reolink NVR

```yaml
reolink:
  enabled: true
  nvr:
    enabled: true
    ip: "192.168.1.100"
    username: "admin"
    password: "your_password"
    port: 554
```

The system will auto-discover all cameras connected to the NVR!

#### Standalone Cameras

```yaml
reolink:
  enabled: true
  cameras:
    - name: "front_camera"
      enabled: true
      ip: "192.168.1.101"
      username: "admin"
      password: "your_password"
      stream_type: "sub"  # Use 'sub' for better performance
      use_camera_ai: true  # Use camera's AI detections
```

### Using Camera's Built-In AI

When `use_camera_ai: true`, the system:
- Leverages Reolink's AI (person, vehicle, animal detection)
- Combines with our advanced AI for enhanced accuracy
- Reduces processing load
- Best of both worlds!

### Features

- **RTSP Streaming**: Direct access to camera feeds
- **Multi-Camera Support**: Monitor multiple cameras simultaneously
- **AI Detection Signals**: Use camera's smart detection events
- **Auto-Discovery**: NVR cameras detected automatically

## Home Assistant Integration

### MQTT Auto-Discovery

The system automatically creates Home Assistant entities:

#### Sensors Created

1. **person_count** - Number of people detected
2. **vehicle_count** - Number of vehicles detected
3. **motion** - Motion detection (binary sensor)
4. **anomaly** - Anomaly detected (binary sensor)
5. **vehicle_speed** - Average vehicle speed
6. **recording** - Recording status
7. **activity_level** - Current activity level

### Configuration

```yaml
home_assistant:
  enabled: true
  mqtt:
    broker: "192.168.1.100"  # Your HA IP
    port: 1883
    username: ""  # Optional
    password: ""
    device_name: "AI Camera System"

  auto_discovery: true

  publish:
    person_detection: true
    vehicle_detection: true
    motion_detection: true
    anomaly_detection: true
    speed_data: true
    activity_level: true
    statistics: true
```

### Home Assistant Automations

Example automation triggers:

```yaml
# Alert on anomaly
automation:
  - alias: "AI Camera Anomaly Alert"
    trigger:
      platform: state
      entity_id: binary_sensor.ai_camera_anomaly
      to: 'on'
    action:
      service: notify.mobile_app
      data:
        message: "Unusual activity detected by AI camera!"

# Alert on person at night
  - alias: "Person Detected at Night"
    trigger:
      platform: state
      entity_id: sensor.ai_camera_person_count
      to: '1'
    condition:
      condition: time
      after: '22:00:00'
      before: '06:00:00'
    action:
      service: notify.mobile_app
      data:
        message: "Person detected at unusual time"

# Speeding vehicle alert
  - alias: "Speeding Vehicle"
    trigger:
      platform: numeric_state
      entity_id: sensor.ai_camera_vehicle_speed
      above: 60
    action:
      service: notify.mobile_app
      data:
        message: "Vehicle speeding detected: {{ states('sensor.ai_camera_vehicle_speed') }} km/h"
```

### Published Events

The system publishes detailed events to MQTT:

```
homeassistant/sensor/ai_camera/events/person
homeassistant/sensor/ai_camera/events/vehicle
homeassistant/sensor/ai_camera/events/anomaly
```

## Database & Analytics

### Data Storage

Everything is stored in SQLite database for analysis:

- **Detections**: All object detections with metadata
- **Person Appearances**: Face recognition history
- **Vehicle Records**: Speed, color, type, direction
- **Anomalies**: Unusual events with severity
- **Activity Log**: Time-based activity tracking

### Analytics Dashboard

Access at: `http://localhost:5000/analytics`

#### Features

1. **Hourly Activity Graph** - Bar chart showing activity by hour
2. **Daily Distribution** - Activity by day of week
3. **Vehicle Speed Chart** - Speed distribution over time
4. **Color Distribution** - Pie chart of vehicle colors
5. **Known People List** - All recognized individuals
6. **Recent Anomalies** - Unusual events timeline
7. **Detection Timeline** - 24-hour activity timeline
8. **Learned Patterns** - AI insights and discoveries

#### Real-Time Updates

Dashboard updates every 5 seconds with:
- Latest detections
- New patterns learned
- Updated statistics
- Recent insights

### Data Retention

```yaml
database:
  cleanup_days: 90  # Keep data for 90 days
```

Automatic cleanup runs daily to remove old data.

## Advanced Features

### Speed Calibration Tool

Accurately measure vehicle speeds:

1. Measure a known distance in camera view
2. Update `pixels_per_meter` in config
3. System calculates real-world speeds
4. Accuracy within 5-10% with proper calibration

### Behavioral Profiling

The system creates behavioral profiles for:
- Each recognized person
- Vehicle patterns
- Time-based activities

### Insights Engine

Generates human-readable insights:
- "Peak activity at 8:00-9:00 AM"
- "John Smith typically appears between 17:00-19:00"
- "Average vehicle speed: 42.3 km/h"
- "Most common vehicle color: Silver (45% of vehicles)"

### Custom Learning Rules

Define what the system should learn:
- Specific time patterns
- Person-specific behaviors
- Vehicle characteristics
- Environmental patterns

## Performance Optimization

### Recommended Settings

For best performance:

```yaml
camera:
  fps: 15  # Lower FPS for better AI processing

performance:
  process_every_n_frames: 2  # Process every 2nd frame

ml_model:
  type: "yolov8n"  # Fastest model
  device: "cuda"   # Use GPU if available

reolink:
  stream_type: "sub"  # Use sub-stream for efficiency
```

### GPU Acceleration

For CUDA-enabled GPUs:
```yaml
ml_model:
  device: "cuda"
```

Speeds up detection by 10-20x!

## Troubleshooting

### Face Recognition Issues

**Problem**: Not recognizing people
**Solution**:
- Lower `tolerance` (try 0.5)
- Ensure good lighting
- Let system collect more samples

**Problem**: Too many false matches
**Solution**:
- Increase `tolerance` (try 0.7)
- Delete and re-learn person

### Behavioral Analysis

**Problem**: No patterns learned
**Solution**:
- Need 100+ events minimum
- Wait 1 week for best results
- Check `min_events_for_learning` setting

### Speed Estimation

**Problem**: Inaccurate speeds
**Solution**:
- Calibrate `pixels_per_meter` correctly
- Ensure camera angle is suitable
- Vehicles should move across frame (not toward camera)

### Home Assistant

**Problem**: Sensors not appearing
**Solution**:
- Check MQTT broker connection
- Verify `auto_discovery: true`
- Restart Home Assistant
- Check MQTT logs

## Best Practices

### 1. Let It Learn

- Give the system 1-2 weeks to learn patterns
- Don't interfere with auto-learning initially
- Review and rename people after auto-learning

### 2. Calibrate Properly

- Measure distances accurately for speed estimation
- Test with known speeds
- Adjust as needed

### 3. Monitor Insights

- Check analytics dashboard daily
- Review learned patterns
- Act on anomaly alerts

### 4. Regular Maintenance

- Review and clean up unknown faces monthly
- Check database size
- Update configurations as needed

### 5. Privacy Considerations

- Store database securely
- Delete people who should not be tracked
- Review retention policies
- Comply with local privacy laws

## API Reference

### Analytics Endpoints

```
GET  /api/analytics/comprehensive  # All analytics data
GET  /api/people                   # Known people
GET  /api/anomalies                # Anomaly history
POST /api/learning/trigger         # Force learning
GET  /api/status                   # System status
```

### Response Examples

#### Comprehensive Analytics
```json
{
  "learning_status": {
    "known_people": 5,
    "total_events": 1523,
    "next_task": "Learn 3 frequently appearing unknown faces"
  },
  "hourly_activity": {
    "8": 45,
    "9": 62,
    "17": 58
  },
  "vehicle_stats": {
    "average_speed": 38.5,
    "max_speed": 65.2,
    "color_distribution": {
      "silver": 12,
      "black": 8,
      "white": 6
    }
  }
}
```

## Support

For issues or questions:
1. Check this documentation
2. Review logs: `camera_system.log`
3. Check GitHub issues
4. Create new issue with logs

## Future Enhancements

Planned features:
- [ ] License plate recognition
- [ ] Pet recognition and tracking
- [ ] Weather condition detection
- [ ] Crowd density analysis
- [ ] Object tracking across cameras
- [ ] Advanced trajectory prediction
- [ ] Natural language queries ("Who visited yesterday?")

---

**Built with ❤️ for the smart home community**
