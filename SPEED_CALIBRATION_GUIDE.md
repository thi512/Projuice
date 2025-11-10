# 🚗 Professional Speed Calibration Guide

## Overview

This AI camera system includes **professional-grade vehicle speed estimation** with three calibration methods:

1. **Simple Global** - Easy setup, basic accuracy
2. **Zone-Based** - Medium difficulty, good accuracy
3. **Homography Perspective Transform** - Advanced setup, **professional-grade accuracy**

## Quick Start

1. **Access Settings**: Navigate to `http://localhost:5000/settings`
2. **Select Method**: Choose your calibration method
3. **Configure**: Follow the on-screen guide
4. **Save**: Settings persist automatically across restarts
5. **Monitor**: View statistics in real-time

---

## Method 1: Simple Global Calibration

### ✅ Best For:
- Quick testing
- Single-lane monitoring
- Non-critical applications

### ⚠️ Limitations:
- Inaccurate for perspective views
- Same calibration for near and far objects
- Error increases with distance from camera

### 📖 Step-by-Step:

1. **Measure a Known Distance**
   - Place two markers on the road (e.g., 5 meters apart)
   - Use a measuring tape or laser measure
   - Mark clearly visible points

2. **Capture a Frame**
   - Take a snapshot from your camera
   - Measure the pixel distance between the markers
   - Use any image editor or screenshot tool

3. **Calculate**
   ```
   pixels_per_meter = measured_pixels / actual_meters
   ```

   **Example:**
   - 5 meters = 250 pixels
   - pixels_per_meter = 250 / 5 = **50**

4. **Enter in Settings**
   - Go to Settings page
   - Select "Simple Global"
   - Enter: `50` in "Pixels Per Meter"
   - Save

### 📊 Expected Accuracy:
- ±20-30% error (depends on perspective)
- Better for objects near camera
- Worse for objects far from camera

---

## Method 2: Zone-Based Calibration

### ✅ Best For:
- Multi-lane roads
- Moderate accuracy requirements
- Good balance between effort and accuracy

### 🎯 How It Works:
Divide the camera view into horizontal zones, each with its own calibration. Objects farther from the camera appear smaller, so they need different calibration values.

### 📖 Step-by-Step:

1. **Analyze Your Camera View**
   ```
   Zone 1 (Far):   y=0    to y=240   ─── Farthest from camera
   Zone 2 (Mid):   y=240  to y=480   ─── Middle distance
   Zone 3 (Near):  y=480  to y=720   ─── Closest to camera
   ```

2. **Calibrate Each Zone**

   **Zone 1 (Far lane/top of image):**
   - Measure a known distance at the top of the frame
   - Example: 5 meters = 125 pixels
   - Calibration: 125 / 5 = **25 pixels/meter**

   **Zone 2 (Middle):**
   - Measure in the middle of the frame
   - Example: 5 meters = 250 pixels
   - Calibration: 250 / 5 = **50 pixels/meter**

   **Zone 3 (Near lane/bottom of image):**
   - Measure at the bottom of the frame
   - Example: 5 meters = 400 pixels
   - Calibration: 400 / 5 = **80 pixels/meter**

3. **Enter in Settings**
   - Select "Zone-Based" method
   - Click "Add Zone" for each zone:
     - Zone 1: Y Min=0, Y Max=240, PPM=25
     - Zone 2: Y Min=240, Y Max=480, PPM=50
     - Zone 3: Y Min=480, Y Max=720, PPM=80
   - Save

### 💡 Tips:
- Use 3-5 zones for best results
- Zones should not overlap
- Higher PPM for areas closer to camera
- Test with known vehicle speeds and adjust

### 📊 Expected Accuracy:
- ±10-15% error
- Much better than simple method
- Good for most applications

---

## Method 3: Homography Perspective Transform

### ✅ Best For:
- Professional installations
- High accuracy requirements
- Traffic enforcement
- Research and analytics

### 🎯 How It Works:
Uses **4 reference points** to compute a mathematical transformation that removes perspective distortion. This is the same method used in professional traffic cameras and sports analytics.

### 📖 Step-by-Step:

#### **Step 1: Prepare Reference Rectangle**

You need a **rectangular area on the road** with **known dimensions**.

**Options:**
- Parking space (standard: 5m × 2.5m)
- Lane markings (standard spacing: 3m or 10m)
- Custom marked rectangle using spray paint/chalk

**Requirements:**
- Rectangle must be parallel to road
- All 4 corners must be visible in camera view
- Clearly defined corners

#### **Step 2: Measure Real-World Dimensions**

Example using a parking space:
- Width: **2.5 meters**
- Length: **5.0 meters**

#### **Step 3: Mark Points in Camera View**

1. Go to Settings page
2. Select "Homography Transform"
3. The camera feed will be displayed
4. Click **4 corners** in this order:
   1. **Bottom-Left** (nearest to camera)
   2. **Bottom-Right** (nearest to camera)
   3. **Top-Left** (farthest from camera)
   4. **Top-Right** (farthest from camera)

#### **Step 4: Enter Real Dimensions**
- Rectangle Width: `2.5` meters
- Rectangle Length: `5.0` meters

#### **Step 5: Compute & Save**
- Click "Compute Homography"
- Click "Save Settings"
- Transformation is automatically applied!

### 🔬 The Math:
```
Homography Matrix (3x3):
┌              ┐
│ h11 h12 h13 │
│ h21 h22 h23 │
│ h31 h32 h33 │
└              ┘

Converts: [x_pixel, y_pixel] → [x_meters, y_meters]
```

The system automatically computes this using `cv2.getPerspectiveTransform()`.

### 💡 Advanced Tips:

**For Maximum Accuracy:**
1. Use the **largest possible reference rectangle** that fits in view
2. Place rectangle in the **center of the monitoring area**
3. Avoid areas with lens distortion (edges of wide-angle cameras)
4. Use a **flat surface** (avoid slopes)
5. **Verify** with a vehicle of known speed

**Multi-Lane Setup:**
- You can use **separate homographies for each lane**
- Define different reference rectangles per lane
- System tracks which lane each vehicle is in

### 📊 Expected Accuracy:
- ±2-5% error
- Professional-grade
- Suitable for enforcement/research
- Consistent across entire view

---

## Camera Parameters (Optional)

These help with understanding your setup but are not required for calibration:

```yaml
Camera Height: 4.0 meters (height above ground)
Distance to Road: 6.0 meters (horizontal distance)
Camera Angle: 30 degrees (downward angle from horizontal)
```

**Used for:**
- Documentation
- Future automatic calibration
- 3D reconstruction

---

## Verification & Testing

### Test Your Calibration:

1. **Known Speed Test**
   - Drive a vehicle at known speed (use GPS speedometer)
   - Compare with system measurement
   - Should be within ±5% for homography, ±15% for zones

2. **Cross-Reference**
   - Compare speeds of same vehicle across different zones
   - Should be consistent with homography method

3. **Statistics Check**
   - View Statistics section in Settings
   - Check if average speeds are realistic
   - Typical residential: 30-50 km/h
   - Typical highway: 80-120 km/h

---

## Settings Storage

All calibration settings are saved to:
```
data/speed_calibration.json
```

**Format:**
```json
{
  "method": "homography",
  "pixels_per_meter": 50,
  "zones": [
    {"y_range": [0, 240], "pixels_per_meter": 25},
    {"y_range": [240, 480], "pixels_per_meter": 50},
    {"y_range": [480, 720], "pixels_per_meter": 80}
  ],
  "homography": {
    "image_points": [[320, 600], [960, 600], [200, 300], [1080, 300]],
    "world_points": [[0, 0], [2.5, 0], [0, 5], [2.5, 5]]
  },
  "camera_height": 4.0,
  "camera_distance": 6.0,
  "camera_angle": 30,
  "last_updated": "2025-11-10T15:30:00"
}
```

**Features:**
- ✅ Persists across system restarts
- ✅ Automatically loaded on startup
- ✅ Backed up with system
- ✅ Can be manually edited

---

## Troubleshooting

### Problem: Speed readings are way too high/low

**Solution:**
- Check your pixels_per_meter calculation
- Verify your reference distance measurement
- Ensure you're using the correct method for your setup

### Problem: Speed varies wildly for same vehicle

**Solution:**
- Use zone-based or homography method
- Simple method has high variance with perspective
- Check that vehicle is tracked consistently

### Problem: Homography shows strange results

**Solution:**
- Verify 4 points form a proper rectangle
- Ensure points are in correct order (bottom-left, bottom-right, top-left, top-right)
- Check that reference dimensions are accurate
- Clear points and try again

### Problem: No speed data showing

**Solution:**
- Check that vehicles are being detected (YOLO)
- Verify speed estimation is enabled in config
- Check logs for errors
- Ensure sufficient FPS (minimum 15-20 fps)

---

## Best Practices

### ✅ DO:
- Calibrate during good lighting conditions
- Use clear, visible reference points
- Test with known speeds
- Recalibrate if camera is moved
- Document your calibration settings

### ❌ DON'T:
- Use very small reference distances (< 2 meters)
- Calibrate in areas with lens distortion
- Rely on simple method for critical applications
- Forget to save settings
- Skip verification testing

---

## Professional Installation Guide

### For Traffic Enforcement / Research:

1. **Camera Positioning**
   - Mount at least 4 meters high
   - Angle downward 20-30 degrees
   - Perpendicular to traffic flow
   - Avoid obstructions

2. **Reference Setup**
   - Use professional surveying tools
   - Mark 10m × 3m reference area
   - Use reflective markers for visibility
   - Document with photographs

3. **Calibration**
   - Use homography method
   - Calibrate in daylight
   - Verify with multiple known speeds
   - Document accuracy measurements

4. **Validation**
   - Test with radar gun
   - Record error margins
   - Adjust if needed
   - Recalibrate quarterly

5. **Documentation**
   - Record all calibration data
   - Save reference photos
   - Document camera specifications
   - Maintain calibration log

---

## API Integration

### Get Current Settings:
```bash
curl http://localhost:5000/api/speed/settings
```

### Update Settings:
```bash
curl -X POST http://localhost:5000/api/speed/settings \
  -H "Content-Type: application/json" \
  -d '{
    "method": "homography",
    "pixels_per_meter": 50,
    "homography": {
      "image_points": [[320, 600], [960, 600], [200, 300], [1080, 300]],
      "world_points": [[0, 0], [2.5, 0], [0, 5], [2.5, 5]]
    }
  }'
```

### Get Statistics:
```bash
curl http://localhost:5000/api/speed/statistics
```

---

## Support

For issues or questions:
- Check the web interface Settings page for guides
- Review statistics to verify operation
- Check system logs for errors
- Consult the main README.md

**Remember:** Accurate speed measurement requires proper calibration. Take time to set it up correctly! 🎯
