# 💬 AI Chatbot Query Guide

## Ask Your Camera System Anything!

The AI Chatbot lets you search through your camera footage using natural language. Instead of browsing through hours of video or complex database queries, just ask questions like you would to a person.

---

## 🚀 Quick Start

### **Access the Chatbot**
```
http://localhost:5000/chat
```

### **Ask a Question**
Simply type your question in plain English:
```
"Show me when someone came to the door today"
```

The AI will:
1. ✅ Understand your question
2. 🔍 Search the database
3. 📊 Return relevant results
4. 💬 Give you a conversational answer

---

## 💡 Example Questions You Can Ask

### **Person Detection Queries**

```
"Show me when someone came to the door today"
→ Returns all person detections from today

"Did anyone visit yesterday?"
→ Shows person appearances from yesterday

"When was John last seen?"
→ Finds most recent detection of person named John

"How many people were detected this week?"
→ Counts total person detections from last 7 days

"Show me all people detected in the last hour"
→ Lists recent person detections

"Who was at the front door at 3pm?"
→ Person detections around specified time
```

### **Vehicle Detection Queries**

```
"Did any cars pass by today?"
→ Returns all vehicle detections from today

"Show me all vehicles from yesterday"
→ Lists vehicles detected yesterday

"How many cars were detected in the last hour?"
→ Counts recent vehicle detections

"Show me all red vehicles"
→ Filters vehicles by color (red)

"Did a blue car go past this morning?"
→ Searches for blue vehicles from today's morning

"Show me vehicles from this week"
→ All vehicle detections from last 7 days
```

### **Speed-Related Queries**

```
"What was the fastest car today?"
→ Shows vehicle with highest speed

"Show me cars that were speeding"
→ Vehicles with speed data

"How fast was that car going?"
→ Speed information for recent vehicles

"Show me all vehicles with speed data"
→ Vehicles where speed was measured
```

### **Color-Specific Queries**

```
"Show me all red cars from today"
→ Red vehicles detected today

"Did a white truck pass by?"
→ White truck detections

"Show me silver vehicles this week"
→ Silver-colored vehicles from last 7 days

"Any black cars yesterday?"
→ Black vehicle detections from yesterday
```

### **Pet Detection Queries**

```
"When was my dog last detected?"
→ Most recent dog detection

"Show me when my cat was outside today"
→ Cat detections from today

"Did my dog go outside in the last hour?"
→ Recent dog/pet activity

"How many times did my pet appear today?"
→ Count of pet detections
```

### **Motion & Activity Queries**

```
"Was there any motion today?"
→ Motion events from today

"Show me all activity from yesterday"
→ All motion/activity from yesterday

"Anything moving in the last hour?"
→ Recent motion events

"When was the last motion detected?"
→ Most recent motion event
```

### **Anomaly & Unusual Activity**

```
"Any unusual activity today?"
→ Shows detected anomalies

"Show me anything suspicious this week"
→ Anomalies from last 7 days

"Were there any alerts?"
→ Anomaly and alert records

"Show me unresolved anomalies"
→ Anomalies that haven't been marked as resolved

"Anything weird yesterday?"
→ Unusual events from yesterday
```

### **Recording Queries**

```
"Show me all recordings from today"
→ Video recordings created today

"What recordings do I have from yesterday?"
→ Recordings from yesterday

"Show me recordings from this week"
→ All recordings from last 7 days

"How many recordings from today?"
→ Count of today's recordings
```

### **Time-Based Queries**

```
"Show me everything from today"
→ All detections from today

"What happened yesterday?"
→ All events from yesterday

"Show me activity from the last hour"
→ Recent detections and events

"What happened in the last 30 minutes?"
→ Very recent activity

"Show me last week's detections"
→ All detections from past 7 days

"Anything from this morning?"
→ Morning detections (time-filtered)
```

---

## 🎯 How the AI Understands Your Questions

### **Intent Detection**
The chatbot identifies what you're looking for:
- **Person Detection**: Questions about people, visitors, someone
- **Vehicle Detection**: Questions about cars, trucks, vehicles
- **Speed**: Questions about how fast, speeding, speed
- **Color**: Questions mentioning colors (red, blue, white, etc.)
- **Pet**: Questions about dogs, cats, pets
- **Anomaly**: Questions about unusual, suspicious, weird activity
- **Motion**: Questions about movement, motion, activity

### **Time Range Extraction**
Automatically understands time references:
- **"today"** → Since midnight today
- **"yesterday"** → Yesterday's date
- **"last hour"** → Past 60 minutes
- **"last 2 hours"** → Past 120 minutes
- **"this week"** → Past 7 days
- **"this month"** → Past 30 days
- **"last 3 days"** → Past 72 hours

### **Entity Extraction**
Pulls out important details:
- **Person names**: "Show me when **John** was detected"
- **Colors**: "Show me **red** vehicles"
- **Vehicle types**: "Did a **truck** go by?"
- **Pet types**: "When was my **dog** seen?"

---

## 📊 Understanding Results

### **Result Types**

#### **Person Detection Result**
```json
{
  "type": "person",
  "name": "John Doe",
  "timestamp": "2024-01-15 14:30:00",
  "confidence": 0.95,
  "is_recognized": true,
  "is_unusual": false
}
```

#### **Vehicle Detection Result**
```json
{
  "type": "vehicle",
  "vehicle_type": "car",
  "color": "red",
  "speed": 45.5,
  "timestamp": "2024-01-15 15:00:00"
}
```

#### **Anomaly Result**
```json
{
  "type": "anomaly",
  "anomaly_type": "unusual_time_activity",
  "severity": 0.7,
  "description": "Person detected at unusual time",
  "timestamp": "2024-01-15 02:30:00",
  "resolved": false
}
```

### **Response Format**

The chatbot gives you:
1. **Conversational Answer**: Human-friendly summary
2. **Detailed Results**: Structured data with all details
3. **Timestamps**: When events occurred
4. **Counts**: How many results found

Example conversation:
```
You: "Show me when someone came to the door today"

AI: "Found 3 person detection(s): John (2x), Unknown (1x)"

Results Panel:
- Person: John - 14:30 (recognized)
- Person: John - 16:45 (recognized)
- Person: Unknown - 18:20 (not recognized)
```

---

## 🔍 Advanced Query Features

### **Combining Filters**

Ask complex questions:
```
"Show me red cars from yesterday"
→ Filters: vehicle type + color + time

"Did John come by in the last 2 hours?"
→ Filters: specific person + time range

"Any unusual vehicle activity today?"
→ Combines anomaly detection with vehicles
```

### **Counting**

Get statistics:
```
"How many people today?"
"Count vehicles this week"
"Number of detections in the last hour"
```

### **Superlatives**

Find extremes:
```
"Fastest car today" → Sorted by speed (highest first)
"Most recent person" → Latest detection
```

---

## 💻 Using the Chat Interface

### **Chat Panel** (Left Side)
- 💬 Type your questions
- 📜 See conversation history
- ⚡ Get instant responses
- 🔄 Maintains context

### **Results Panel** (Right Side)
- 📊 Structured results
- 🏷️ Color-coded by type
- 🕐 Timestamps (relative and absolute)
- 📹 Video playback (for recordings)

### **Example Queries** (Top Bar)
Click any example to try it instantly:
- "Show me when someone came to the door today"
- "Did any cars pass by in the last hour?"
- "When was my dog last detected?"
- etc.

---

## 🎨 Query Tips & Best Practices

### **✅ Good Queries**

**Specific and clear:**
```
"Show me red cars from yesterday" ✅
"When was John detected today?" ✅
"How many people in the last hour?" ✅
```

**Natural language:**
```
"Did anyone visit?" ✅
"Was there motion?" ✅
"Anything unusual?" ✅
```

### **❌ Queries to Avoid**

**Too vague:**
```
"Show me stuff" ❌
"What happened?" ❌ (better: "What happened today?")
```

**Overly complex:**
```
"Show me red cars OR blue trucks from yesterday between 2pm and 4pm unless it was raining" ❌
```

Instead, ask multiple simpler questions:
```
"Show me red cars from yesterday" ✅
"Show me blue trucks from yesterday" ✅
```

---

## 🧠 How It Works

### **Natural Language Processing Pipeline**

```
Your Question
    ↓
Intent Detection (what are you asking about?)
    ↓
Time Extraction (when?)
    ↓
Entity Extraction (who/what specifically?)
    ↓
Database Query (search)
    ↓
Results Formatting (human-readable response)
    ↓
Display Results
```

### **Example Breakdown**

**Question:** *"Show me red cars from yesterday"*

1. **Intent**: vehicle_detection + vehicle_color
2. **Time**: yesterday (2024-01-14 00:00:00 to 23:59:59)
3. **Entities**: color = "red", object_type = "vehicle"
4. **Query**: Search VehicleRecords WHERE color LIKE '%red%' AND timestamp BETWEEN ...
5. **Response**: "Found 5 red vehicle(s). Most recent at 18:30"

---

## 📈 Chatbot Capabilities

### **What It CAN Do**
- ✅ Search person detections by name or time
- ✅ Find vehicles by color, type, speed
- ✅ Detect anomalies and unusual activity
- ✅ Search motion events
- ✅ Find recordings by date/time
- ✅ Count detections
- ✅ Understand natural time references
- ✅ Extract colors, names, types from questions
- ✅ Sort and filter results

### **Current Limitations**
- ⚠️ Video playback requires additional setup
- ⚠️ Time parsing limited to common phrases
- ⚠️ Doesn't understand very complex multi-part queries
- ⚠️ Limited to English language

---

## 🔧 Configuration

### **Enable/Disable Chatbot**

In `config.yaml`:
```yaml
database:
  enabled: true  # Chatbot requires database

web_interface:
  enable_chatbot: true  # Enable/disable chat interface
```

### **Chatbot is automatically enabled when:**
- ✅ Database is enabled
- ✅ System has detection history
- ✅ Web server is running

---

## 🐛 Troubleshooting

### **"Chatbot not initialized" Error**
**Problem**: Database not enabled or not available

**Solution**:
```yaml
# In config.yaml
database:
  enabled: true
  url: "sqlite:///data/camera_system.db"
```

### **"No results found" for Recent Events**
**Problem**: No detections in database yet

**Solution**:
- Let system run for a while to collect data
- Check that detection is enabled
- Verify camera is working

### **Time Queries Not Working**
**Problem**: Time parsing failed

**Try**:
- Use simpler time references: "today", "yesterday"
- Be more specific: "last 2 hours" instead of "recently"
- Use exact times if needed: "Show me detections from today"

### **Can't Find Specific Person**
**Problem**: Person not in database or name mismatch

**Solution**:
- Check person's name in face recognition system
- Try: "Show me all people today" to see what names exist
- Make sure face recognition is enabled

---

## 💡 Pro Tips

### **1. Start Broad, Then Narrow**
```
"Show me people today" → See all results
"Show me when John appeared today" → Filter to specific person
```

### **2. Use Relative Time for Recent Events**
```
"last hour" → Faster than specifying exact times
"today" → Easy to remember
```

### **3. Check Anomalies Daily**
```
"Any unusual activity today?"
→ Quick security check
```

### **4. Track Patterns**
```
"How many people today?"
"How many people yesterday?"
→ Compare activity levels
```

### **5. Monitor Vehicle Activity**
```
"Show me vehicles this week"
→ See traffic patterns
```

### **6. Find Your Pets**
```
"When was my dog outside today?"
→ Track pet activity
```

---

## 🎯 Real-World Use Cases

### **Home Security**
```
"Any unusual activity while I was away?"
"Who was at the door today?"
"Show me all people detected this week"
```

### **Package Tracking**
```
"Did the delivery person come?"
"Anyone at the door this afternoon?"
```

### **Pet Monitoring**
```
"When was my dog last outside?"
"How many times did my cat appear today?"
```

### **Traffic Monitoring**
```
"How many cars today?"
"Show me speeding vehicles"
"Red cars from this week"
```

### **Daily Review**
```
"What happened today?"
"Show me all activity from yesterday"
"Any unusual events this week?"
```

---

## 🚀 Future Enhancements

Coming soon:
- 🎥 **Direct video playback** from results
- 📍 **Location-based queries** ("Show me front camera detections")
- 🔔 **Alert creation** ("Notify me when John arrives")
- 📊 **Statistical queries** ("Average cars per day this week")
- 🌍 **Multi-language support**
- 🤖 **Advanced AI** with GPT integration for even better understanding
- 📱 **Mobile interface** for chat

---

## 📚 Related Documentation

- **[AI_FEATURES.md](AI_FEATURES.md)** - Overview of all AI capabilities
- **[INTERACTIVE_LEARNING.md](INTERACTIVE_LEARNING.md)** - Train custom models
- **[README.md](README.md)** - System overview and setup
- **[INSTALL.md](INSTALL.md)** - Installation instructions

---

## 🆘 Need Help?

**Ask the chatbot itself!**
```
"Show me how to search for people"
"What can I ask you?"
"Help with queries"
```

**Check the logs:**
```bash
tail -f camera_system.log | grep -i chat
```

**Test your database:**
```bash
python -c "from src.database import DatabaseManager; db = DatabaseManager(); print(db.get_detection_count())"
```

---

**Built with ❤️ for the smart home community**

The AI Chatbot makes your camera system truly intelligent - just ask and it delivers! 🚀💬
