# 🔢 License Plate Recognition & 📧 Email Reporting Guide

## Complete Guide to LPR and Automated Email Reports

---

## 📋 Table of Contents

1. [License Plate Recognition (LPR)](#license-plate-recognition)
2. [Email Reporting System](#email-reporting-system)
3. [Configuration](#configuration)
4. [Chatbot Queries](#chatbot-queries)
5. [Troubleshooting](#troubleshooting)

---

## 🔢 License Plate Recognition

### **What is LPR?**

**Automatic License Plate Recognition (ALPR)** uses state-of-the-art OCR (Optical Character Recognition) to detect and read license plates from your camera footage.

### **Key Features**

✅ **State-of-the-Art OCR** - Uses EasyOCR with GPU acceleration
✅ **Multi-Language Support** - Works with plates from different countries
✅ **High Accuracy** - Advanced preprocessing for varied lighting conditions
✅ **Smart Validation** - Validates plates against known formats
✅ **Database Tracking** - Stores all plate detections with metadata
✅ **Trend Analysis** - Identifies patterns and suspicious activity
✅ **Chatbot Integration** - Query plates with natural language

### **How It Works**

```
Vehicle Detection → Crop Region → Preprocess Image → OCR Analysis → Validate Format → Store in Database
```

1. **Vehicle Detection**: YOLO detects vehicles
2. **ROI Extraction**: Crops vehicle region for plate detection
3. **Preprocessing**: Enhances image (denoise, threshold, morph operations)
4. **OCR**: EasyOCR reads text from preprocessed image
5. **Cleaning**: Removes spaces, corrects common OCR errors
6. **Validation**: Checks against country-specific formats
7. **Storage**: Saves to database with vehicle info

### **Supported Plate Formats**

#### **United States** (`country_format: 'us'`)
- ABC1234 (3 letters + 4 numbers)
- AB12345 (2 letters + 5 numbers)
- 123ABC (3 numbers + 3 letters)

#### **United Kingdom** (`country_format: 'uk'`)
- AB12CDE (current format)
- A123BCD (old format)

#### **European** (`country_format: 'eu'`)
- Various formats with 1-3 letters + 1-4 numbers

#### **Auto Mode** (`country_format: 'auto'`)
- Accepts any alphanumeric combination
- Recommended for maximum flexibility

### **Configuration**

In `config.yaml`:

```yaml
license_plate_recognition:
  enabled: true
  languages: ['en']  # OCR languages
  gpu: true  # Use GPU for faster processing
  confidence_threshold: 0.5  # Min confidence (0.0-1.0)
  country_format: 'auto'  # auto, us, uk, eu
```

### **Supported Languages**

EasyOCR supports 80+ languages:

- **English**: `en`
- **Chinese (Simplified)**: `ch_sim`
- **Chinese (Traditional)**: `ch_tra`
- **Japanese**: `ja`
- **Korean**: `ko`
- **Arabic**: `ar`
- **And many more...**

Example for multi-language:
```yaml
languages: ['en', 'ch_sim']  # English + Chinese
```

### **Performance**

| Hardware | Processing Speed | Accuracy |
|----------|-----------------|----------|
| RTX 4070 Ti (GPU) | ~100ms/plate | 95%+ |
| CPU Only | ~500ms/plate | 95%+ |

### **Database Schema**

Plates are stored in the `license_plates` table:

```sql
CREATE TABLE license_plates (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    plate_number VARCHAR(20),  -- Cleaned plate number
    confidence FLOAT,          -- OCR confidence
    vehicle_type VARCHAR(50),   -- car, truck, etc.
    vehicle_color VARCHAR(50),  -- red, blue, etc.
    vehicle_id VARCHAR(100),    -- Link to vehicle record
    country VARCHAR(10),        -- Country code
    camera_id VARCHAR(50),      -- Which camera
    bbox JSON,                  -- Plate bounding box
    raw_text VARCHAR(50),       -- Original OCR text
    metadata JSON               -- Additional data
);
```

---

## 📧 Email Reporting System

### **Overview**

Automated email reporting sends **beautiful HTML reports** on customizable schedules via SMTP. Works with any email provider!

### **Key Features**

✅ **Universal SMTP Support** - Gmail, Outlook, Yahoo, custom servers
✅ **Scheduled Reports** - Daily, weekly, custom schedules
✅ **Beautiful HTML Templates** - Professional-looking emails
✅ **License Plate Reports** - Dedicated plate activity summaries
✅ **Anomaly Alerts** - Instant emails for suspicious activity
✅ **Multiple Recipients** - Send to entire team
✅ **Attachment Support** - Add PDFs, images, etc.
✅ **TLS/SSL Security** - Encrypted email transmission

### **Report Types**

#### **1. Daily Summary Report**
- Total detections
- Person count
- Vehicle count
- License plates recognized
- Anomalies detected
- Top license plates

**Schedule**: Every day at 8:00 AM (configurable)

#### **2. Weekly Summary Report**
- 7-day statistics
- Daily breakdown chart
- Most frequent license plates
- Trend analysis

**Schedule**: Every Monday at 9:00 AM (configurable)

#### **3. License Plate Activity Report**
- Today's plate detections
- Unique vehicles
- Most frequent plates
- Suspicious patterns (if any)

**Schedule**: Every day at 6:00 PM (configurable)

#### **4. Instant Anomaly Alerts**
- Sent immediately when anomaly detected
- Severity level
- Description
- Timestamp

**Trigger**: Real-time (when anomaly occurs)

### **Email Provider Setup**

#### **Gmail**

1. **Enable 2-Step Verification**:
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the 16-character password

3. **Config**:
```yaml
email_reporting:
  enabled: true
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  use_tls: true
  username: "your.email@gmail.com"
  password: "xxxx xxxx xxxx xxxx"  # App password
  from_email: "your.email@gmail.com"
```

#### **Outlook / Office 365**

```yaml
email_reporting:
  enabled: true
  smtp_server: "smtp.office365.com"
  smtp_port: 587
  use_tls: true
  username: "your.email@outlook.com"
  password: "your_password"  # Regular password works
  from_email: "your.email@outlook.com"
```

#### **Yahoo Mail**

```yaml
email_reporting:
  enabled: true
  smtp_server: "smtp.mail.yahoo.com"
  smtp_port: 587
  use_tls: true
  username: "your.email@yahoo.com"
  password: "app_password"  # Generate at Yahoo
  from_email: "your.email@yahoo.com"
```

#### **Custom SMTP Server**

```yaml
email_reporting:
  enabled: true
  smtp_server: "mail.yourdomain.com"
  smtp_port: 587  # Or 465 for SSL, 25 for no encryption
  use_tls: true
  username: "alerts@yourdomain.com"
  password: "your_password"
  from_email: "alerts@yourdomain.com"
```

### **Port Configuration**

| Port | Protocol | Description |
|------|----------|-------------|
| 587 | STARTTLS | **Recommended** - TLS encryption |
| 465 | SSL/TLS | Implicit SSL |
| 25 | None | No encryption (not recommended) |

### **Schedule Configuration**

```yaml
schedules:
  # Daily summary
  daily_summary:
    enabled: true
    time: "08:00"  # 24-hour format

  # Weekly summary
  weekly_summary:
    enabled: true
    day: "monday"  # monday-sunday
    time: "09:00"

  # License plate report
  license_plate_report:
    enabled: true
    time: "18:00"  # 6 PM

  # Custom schedule
  custom_afternoon_report:
    enabled: true
    time: "14:30"  # 2:30 PM
```

### **Multiple Recipients**

```yaml
recipients:
  - "security@company.com"
  - "admin@company.com"
  - "your.personal@gmail.com"
```

### **Instant Alerts Configuration**

```yaml
instant_alerts:
  send_on_anomaly: true
  send_on_suspicious_plate: true
  min_severity: 0.7  # 0.0-1.0 (only alert high severity)
```

---

## 📊 Chatbot Queries for License Plates

### **General Plate Queries**

```
"Show me all license plates today"
→ Returns all plate detections from today

"How many license plates were detected?"
→ Count of total plates

"Show me license plates from this week"
→ Plates from last 7 days

"Any license plates in the last hour?"
→ Recent plate detections
```

### **Specific Plate Queries**

```
"Show me license plate ABC1234"
→ Find specific plate

"Has plate XYZ7890 been detected?"
→ Search for specific plate

"When was plate ABC123 last seen?"
→ Most recent detection of that plate
```

### **Trend Queries**

```
"What are the most frequent license plates?"
→ Top plates by appearance count

"Show me new license plates today"
→ Plates not seen before

"Any suspicious license plates?"
→ Plates with unusual patterns
```

### **Combined Queries**

```
"Show me red car license plates"
→ Plates from red vehicles

"License plates from yesterday morning"
→ Time-filtered results

"How many unique plates this week?"
→ Count distinct plates
```

---

## 🎨 Email Report Examples

### **Daily Summary Email**

```
Subject: Daily Summary Report - January 15, 2025

┌─────────────────────────────────┐
│   📊 Daily Summary Report       │
│   Monday, January 15, 2025      │
└─────────────────────────────────┘

Total Detections: 342
👤 People Detected: 45
🚗 Vehicles Detected: 89
🔢 License Plates Recognized: 67

Top License Plates Today:
━━━━━━━━━━━━━━━━━━━━━━━━━━━
ABC1234  |  5 appearances
XYZ7890  |  3 appearances
DEF4567  |  2 appearances
```

### **License Plate Report Email**

```
Subject: License Plate Report - January 15, 2025

┌─────────────────────────────────┐
│  🔢 License Plate Report        │
│   January 15, 2025              │
└─────────────────────────────────┘

Total Plates Detected: 67
Unique Vehicles: 52

Most Frequent Plates:
━━━━━━━━━━━━━━━━━━━━━━━━━━━
ABC1234  |  5x
XYZ7890  |  3x
DEF4567  |  2x

⚠️ Suspicious Activity
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plate ABC1234 detected 5 times in 1 hour
Plate GHI9012 seen at unusual time (3:15 AM)
```

### **Anomaly Alert Email**

```
Subject: ⚠️ Security Alert: unusual_time_activity

┌─────────────────────────────────┐
│  ⚠️ Security Alert              │
└─────────────────────────────────┘

Type: unusual_time_activity
Severity: 85%
Description: License plate detected at unusual time (2:30 AM)
Time: 2025-01-15 02:30:15

Plate: ABC1234
Vehicle: Blue sedan
```

---

## ⚙️ Complete Configuration Example

```yaml
# License Plate Recognition
license_plate_recognition:
  enabled: true
  languages: ['en']
  gpu: true
  confidence_threshold: 0.5
  country_format: 'auto'

# Email Reporting
email_reporting:
  enabled: true

  # SMTP Configuration (Gmail example)
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  use_tls: true
  username: "mycamera@gmail.com"
  password: "xxxx xxxx xxxx xxxx"  # App password
  from_email: "mycamera@gmail.com"
  from_name: "Home AI Camera"

  # Recipients
  recipients:
    - "security@home.com"
    - "admin@home.com"

  # Schedules
  schedules:
    daily_summary:
      enabled: true
      time: "08:00"

    weekly_summary:
      enabled: true
      day: "monday"
      time: "09:00"

    license_plate_report:
      enabled: true
      time: "18:00"

  # Instant alerts
  instant_alerts:
    send_on_anomaly: true
    send_on_suspicious_plate: true
    min_severity: 0.7
```

---

## 🐛 Troubleshooting

### **License Plate Recognition Issues**

#### **Problem: Plates not being detected**

**Solutions**:
1. Check if LPR is enabled:
   ```yaml
   license_plate_recognition:
     enabled: true
   ```

2. Verify vehicle detection is working (LPR depends on it)

3. Lower confidence threshold:
   ```yaml
   confidence_threshold: 0.3  # Lower = more detections
   ```

4. Check camera positioning (plates should be clearly visible)

#### **Problem: Incorrect plate readings**

**Solutions**:
1. Improve lighting conditions
2. Use higher resolution camera/stream
3. Adjust country format:
   ```yaml
   country_format: 'us'  # More strict validation
   ```

4. Check OCR language settings

#### **Problem: GPU not being used**

**Solutions**:
1. Install CUDA toolkit
2. Verify PyTorch GPU support:
   ```python
   import torch
   print(torch.cuda.is_available())
   ```

3. Set GPU flag:
   ```yaml
   gpu: true
   ```

### **Email Reporting Issues**

#### **Problem: Emails not sending**

**Solutions**:
1. **Check SMTP credentials**:
   ```bash
   # Test connection
   telnet smtp.gmail.com 587
   ```

2. **Verify email enabled**:
   ```yaml
   email_reporting:
     enabled: true
   ```

3. **Check firewall**: Ensure port 587 (or 465) is open

4. **Gmail-specific**: Use App Password, not regular password

#### **Problem: Authentication failed**

**Solutions**:
1. **Gmail**: Generate new App Password
2. **Outlook**: Check if 2FA is enabled
3. **Yahoo**: Enable "Less secure app access"
4. **Check username/password** in config

#### **Problem: Emails going to spam**

**Solutions**:
1. Add sender to contacts
2. Mark first email as "Not Spam"
3. Configure SPF/DKIM records (for custom domains)

#### **Problem: Reports not scheduled correctly**

**Solutions**:
1. Verify time format (24-hour):
   ```yaml
   time: "08:00"  # Correct
   time: "8:00 AM"  # Wrong!
   ```

2. Check timezone (system uses local time)

3. Restart system after config changes

### **Database Issues**

#### **Problem: Plate data not being stored**

**Solutions**:
1. Check database is enabled:
   ```yaml
   database:
     enabled: true
   ```

2. Verify database file exists:
   ```bash
   ls -la data/camera_system.db
   ```

3. Check permissions:
   ```bash
   chmod 644 data/camera_system.db
   ```

### **Performance Issues**

#### **Problem: LPR is slow**

**Solutions**:
1. **Enable GPU**:
   ```yaml
   gpu: true
   ```

2. **Process fewer frames**:
   ```yaml
   performance:
     process_every_n_frames: 5  # Process every 5th frame
   ```

3. **Use faster OCR language** (English only instead of multiple)

4. **Upgrade hardware** (GPU recommended)

---

## 📊 Analytics & Trends

### **Suspicious Pattern Detection**

The system automatically identifies:

1. **Frequent Passes**: Same plate multiple times in short period
2. **Unusual Times**: Plates detected at odd hours (2am-5am)
3. **New Plates**: First-time detections
4. **Loitering**: Same plate staying in view for extended time

### **Trend Analysis**

Access via:
- **Chatbot**: "Show me license plate trends"
- **Analytics Dashboard**: http://localhost:5000/analytics
- **Email Reports**: Weekly summary includes trends

---

## 🚀 Best Practices

### **For License Plate Recognition**

1. **Camera Positioning**:
   - Mount at 5-10 feet height
   - Angle 10-20 degrees downward
   - Ensure good lighting (IR illuminator for night)

2. **Resolution**:
   - Minimum: 720p
   - Recommended: 1080p
   - Optimal: 4K (if GPU available)

3. **Frame Rate**:
   - 15-30 FPS recommended
   - Higher = better accuracy but more processing

### **For Email Reporting**

1. **Use App Passwords**: Never use main account password
2. **Test First**: Send test email before enabling schedules
3. **Monitor Spam Folder**: First few emails might go there
4. **Limit Recipients**: Too many can trigger spam filters
5. **Schedule Wisely**: Don't spam users with too many reports

### **Security**

1. **Use TLS/SSL**: Always encrypt email transmission
2. **Protect Credentials**: Use environment variables:
   ```bash
   export EMAIL_PASSWORD="your_app_password"
   ```

3. **Restrict Access**: Only authorized people should get reports

---

## 💡 Pro Tips

### **Maximize LPR Accuracy**

```yaml
license_plate_recognition:
  enabled: true
  languages: ['en']  # Single language = faster
  gpu: true  # GPU = 5x faster
  confidence_threshold: 0.6  # Higher = fewer false positives
  country_format: 'us'  # Strict validation for your region
```

### **Optimize Email Schedules**

**Daily Summary**: Morning (8am) - Review overnight activity
**Weekly Summary**: Monday morning (9am) - Start week informed
**Plate Report**: Evening (6pm) - End of day summary
**Instant Alerts**: Real-time - Critical events only

### **Custom Queries**

Use chatbot for ad-hoc analysis:
```
"Show me all plates between 2am and 5am this week"
"How many times has plate ABC1234 appeared this month?"
"List all suspicious plate activity"
```

---

## 📚 Related Documentation

- **[README.md](README.md)** - System overview
- **[AI_FEATURES.md](AI_FEATURES.md)** - All AI capabilities
- **[CHATBOT_GUIDE.md](CHATBOT_GUIDE.md)** - Chatbot query guide
- **[INSTALL.md](INSTALL.md)** - Installation instructions

---

## 🆘 Getting Help

**Test your configuration:**
```bash
python -c "from src.email_reporting import EmailReporter; from src.config import load_config; config = load_config(); reporter = EmailReporter(config); reporter.test_email_connection()"
```

**Check logs:**
```bash
tail -f camera_system.log | grep -i "plate\|email"
```

**Verify database:**
```bash
sqlite3 data/camera_system.db "SELECT COUNT(*) FROM license_plates;"
```

---

**Built for smart home security and automation! 🏠🔐**
