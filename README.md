# Mac Sentinel - Lid Closure Alarm

A macOS security web application that detects and alarms when a MacBook's lid begins to close while the system is armed.

## Features

- **Automatic Alarm** - Plays loud alarm when lid closes while armed
- **Sleep Prevention** - Keeps system awake while armed
- **Volume Control** - Automatically sets volume to maximum when alarm triggers
- **Web Interface** - Simple local web UI for ARM/STOP controls
- **Local Only** - Runs on localhost for security

## Requirements

- **macOS** (Apple Silicon or Intel)
- **Python 3.7+**
- **Alarm sound file** (`static/sounds/alarm.mp3`)
- **Amphetamine** (Required for audio playback with lid closed) - [Download from Mac App Store](https://apps.apple.com/app/amphetamine/id937984704)

## Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd MacSentinel
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Add Alarm Sound File

Place an alarm sound file at:
```
static/sounds/alarm.mp3
```

Supported formats: `.mp3`, `.wav`, `.aiff`, `.m4a`

You can download a free alarm sound from [freesound.org](https://freesound.org) or use any audio file.

### 5. Install and Configure Amphetamine (Required for Audio with Lid Closed)

⚠️ **Important**: macOS disables built-in speakers when the lid closes. To enable audio playback with the lid closed, you need Amphetamine.

1. **Install Amphetamine:**
   - Download from the [Mac App Store](https://apps.apple.com/app/amphetamine/id937984704)
   - Launch Amphetamine (a pill icon will appear in your menu bar)

2. **Configure Amphetamine:**
   - Click the Amphetamine icon in the menu bar
   - Select **"Quick Preferences"** or **"Preferences"**
   - **Uncheck** "Allow system sleep when display is closed"
   - Start a session by clicking the icon and selecting **"Indefinitely"** or set a specific duration

3. **Verify Setup:**
   - With Amphetamine running, close your MacBook lid
   - Audio should continue to play (test with any audio file)
   - If audio stops, check Amphetamine settings

**Note**: Without Amphetamine, the alarm will trigger but audio will only play when the lid is reopened.

## Usage

### 1. Start the Server

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### 2. Open the Web Interface

Open your browser and navigate to:
```
http://127.0.0.1:5000
```
or
```
http://localhost:5000
```


### 3. Start Amphetamine

**Before arming the system**, make sure Amphetamine is running:
1. Check the menu bar for the Amphetamine icon (pill shape)
2. If not running, launch Amphetamine and start a session
3. Verify "Allow system sleep when display is closed" is **unchecked** in preferences

### 4. Arm the System

1. Click the **ARM** button
2. The system will:
   - Start preventing sleep (`caffeinate`)
   - Begin monitoring for lid close events
   - Status will change to "ARMED" (red)

### 4. Test the Alarm

You can test the alarm in two ways:

**Option A: Manual Test (Recommended for first test)**
- Open browser console (F12) or use terminal:
  ```bash
  curl -X POST http://127.0.0.1:5000/api/test-alarm
  ```
- The alarm should start playing immediately

**Option B: Real Test**
- Make sure system is **ARMED** (status shows "ARMED")
- Close your MacBook lid
- The alarm should trigger automatically
- Open lid and click **STOP** to disarm

### 6. Stop/Disarm

1. Click the **STOP** button
2. The system will:
   - Stop the alarm (if playing)
   - Stop sleep prevention
   - Stop monitoring
   - Status will change to "DISARMED" (green)

## How It Works

1. **ARM** → Starts `caffeinate` (prevents sleep) + starts power monitoring thread
2. **Lid Close Detected** → Power monitor detects clamshell/sleep event
3. **Alarm Triggers** → Sets volume to 100% + plays alarm sound in loop
4. **STOP** → Stops alarm + stops caffeinate + stops monitoring

## Technical Details

- **Power Monitoring**: Uses `pmset -g log` to detect clamshell close and sleep events
- **Sleep Prevention**: Uses `caffeinate -d -i` to prevent display and idle sleep
- **Volume Control**: Uses `osascript` to set system volume to 100%
- **Alarm Playback**: Uses `afplay -l` to loop alarm sound

## Troubleshooting

### Alarm doesn't trigger when lid closes

- Make sure the system is **ARMED** (status shows "ARMED")
- Check terminal output for "Power monitoring started"
- Verify `pmset` command works: `pmset -g log`
- Check if alarm sound file exists: `ls static/sounds/alarm.mp3`

### Alarm sound doesn't play

- **Make sure Amphetamine is running** and configured correctly (see Installation step 5)
- Verify alarm file exists and is readable
- Check file format (should be `.mp3`, `.wav`, `.aiff`, or `.m4a`)
- Test manually: `afplay static/sounds/alarm.mp3`
- Check volume isn't muted
- If lid is closed: Test that audio plays with lid closed (Amphetamine must be active)

### System still sleeps when armed

- Verify `caffeinate` is running: `ps aux | grep caffeinate`
- Check terminal for "Caffeinate started" message
- Try manually: `caffeinate -d -i` (should prevent sleep)

### Port 5000 already in use

- Stop other Flask apps or change port in `app.py`:
  ```python
  app.run(debug=True, host='127.0.0.1', port=5001)  # Change to 5001
  ```

## Testing Checklist

Follow these steps to verify everything works:

### ✅ Pre-Test Checks

1. **Verify alarm file exists:**
   ```bash
   ls static/sounds/alarm.mp3
   ```

2. **Test alarm sound manually:**
   ```bash
   afplay static/sounds/alarm.mp3
   ```
   (Press Ctrl+C to stop)

3. **Check pmset works:**
   ```bash
   pmset -g log | tail -5
   ```

### ✅ Test 1: Manual Alarm Trigger

1. Start server: `python app.py`
2. Open browser: `http://127.0.0.1:5000`
3. Click **ARM** button
4. Check terminal for:
   - "Caffeinate started"
   - "Power monitoring started"
5. Test alarm manually:
   ```bash
   curl -X POST http://127.0.0.1:5000/api/test-alarm
   ```
6. Alarm should play - verify volume is at 100%
7. Click **STOP** button
8. Alarm should stop

### ✅ Test 2: Real Lid Close Detection

1. Make sure server is running and system is **ARMED**
2. Check terminal shows "Power monitoring started"
3. **Carefully** close your MacBook lid (don't fully close - just enough to trigger sensor)
4. Watch terminal - should see "LID CLOSE DETECTED"
5. Alarm should trigger automatically
6. Open lid
7. Click **STOP** to disarm

### ✅ Test 3: Sleep Prevention

1. ARM the system
2. Check caffeinate is running:
   ```bash
   ps aux | grep caffeinate
   ```
3. Wait 1-2 minutes - system should NOT sleep
4. STOP the system
5. System should be able to sleep normally again

## Security Note

This app runs on `localhost` (127.0.0.1) only and is not accessible from other devices. This is intentional for security - the app controls your Mac's hardware and should only be accessible locally. 
