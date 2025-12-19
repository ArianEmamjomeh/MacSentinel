# Mac Sentinel - Lid Closure Alarm

A macOS security web application that detects and alarms when a MacBook's lid begins to close while the system is armed.

## Features

- **Automatic Alarm** - Plays loud alarm when lid closes while armed
- **Sleep Prevention** - Keeps system awake while armed
- **Volume Control** - Automatically sets volume to maximum when alarm triggers
- **Web Interface** - Simple web UI for ARM/STOP controls
- **Deployable** - Can run locally or on a network

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

**For local use only:**
```bash
python app.py
```

**For network access (deployment):**
```bash
# Edit app.py and change the last line to:
app.run(debug=False, host='0.0.0.0', port=5000)
```

Then start:
```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on/off
```

### 2. Open the Web Interface

**Local access:**
```
http://127.0.0.1:5000
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

## Deployment

### Local Development (Default)

By default, the app runs on `127.0.0.1` (localhost only) for security during development.

### Network Deployment

To deploy on your local network:

1. **Update `app.py`** - Change the last line:
   ```python
   # Change from:
   app.run(debug=True, host='127.0.0.1', port=5000)
   
   # To:
   app.run(debug=False, host='0.0.0.0', port=5000)
   ```

2. **Find your Mac's IP address:**
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

3. **Access from other devices:**
   ```
   http://<your-mac-ip>:5000
   ```

### Production Deployment Options

**Option 1: Using Gunicorn (Recommended)**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Option 2: Using systemd (Auto-start on boot)**
Create a service file to run the app automatically.

**Option 3: Using a reverse proxy (nginx)**
Set up nginx to proxy requests to the Flask app.

### Security Considerations

⚠️ **Important Security Notes:**

- **Add Authentication**: The current version has no authentication. Anyone with network access can ARM/STOP the system.
- **Use HTTPS**: If deploying over the internet, use HTTPS (via nginx with Let's Encrypt).
- **Firewall**: Consider restricting access to specific IP addresses.
- **Password Protection**: Consider adding basic auth or a password system before deploying publicly.

**Recommended for production:**
- Add authentication (Flask-Login, Flask-HTTPAuth, or similar)
- Use a production WSGI server (Gunicorn, uWSGI)
- Set up HTTPS/SSL
- Configure firewall rules
- Use environment variables for sensitive config

## License

[Add your license here]

## Contributing

[Add contribution guidelines if needed]
