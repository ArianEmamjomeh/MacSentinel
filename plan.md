# Mac Lid-Closure Alarm - Development Plan

## Project Overview
A macOS security web application that detects and alarms when a MacBook's lid begins to close while the system is armed. The app runs entirely locally and uses macOS power event monitoring instead of restricted motion sensors.

---

## Architecture Components

### 1. **Flask Web Server**
- Local HTTP server (localhost)
- RESTful API endpoints for ARM/STOP
- Serves static HTML/CSS/JS frontend
- Manages armed state

### 2. **Power Event Monitor**
- Background thread watching macOS power logs
- Uses `pmset` to detect:
  - Clamshell (lid close) events
  - Sleep/wake events
- Triggers alarm when events detected while armed

### 3. **Sleep Prevention**
- Uses `caffeinate` command to prevent system sleep
- Activated when armed
- Deactivated when disarmed

### 4. **Alarm System**
- Sets system volume to 100% (via `osascript`)
- Plays alarm sound (via `afplay`)
- Continues until user stops

### 5. **Web UI**
- Simple, clean interface
- ARM button (starts monitoring)
- STOP button (stops alarm and disarms)
- Status indicator (armed/disarmed)

---

## File Structure

```
MacSentinel/
├── README.md
├── plan.md
├── requirements.txt
├── app.py                 # Main Flask application
├── power_monitor.py       # Power event monitoring logic
├── alarm.py               # Alarm triggering and control
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── sounds/
│       └── alarm.mp3      # Alarm sound file
└── templates/
    └── index.html
```

---

## Implementation Phases

### Phase 1: Project Setup
- [ ] Create virtual environment
- [ ] Create `requirements.txt` with Flask dependency
- [ ] Set up project directory structure
- [ ] Create basic Flask app skeleton

### Phase 2: Core Flask Server
- [ ] Implement Flask app with routes:
  - `GET /` - Serve main page
  - `POST /api/arm` - Arm the system
  - `POST /api/stop` - Stop/disarm the system
  - `GET /api/status` - Get current armed status
- [ ] Implement armed state management (in-memory or simple file)
- [ ] Add CORS handling if needed

### Phase 3: Power Event Monitoring
- [ ] Create `power_monitor.py` module
- [ ] Implement `pmset` log monitoring:
  - Use `pmset -g log` or `pmset -g log | grep` to watch for events
  - Parse clamshell close events
  - Parse sleep/wake events
- [ ] Create background thread that:
  - Continuously monitors power logs
  - Checks armed state
  - Triggers alarm callback when event detected
- [ ] Handle thread lifecycle (start/stop with armed state)

### Phase 4: Sleep Prevention
- [ ] Implement `caffeinate` subprocess management
- [ ] Start `caffeinate` process when arming
- [ ] Terminate `caffeinate` process when disarming
- [ ] Handle process cleanup on app exit

### Phase 5: Alarm System
- [ ] Create `alarm.py` module
- [ ] Implement volume control:
  - Use `osascript -e "set volume output volume 100"`
- [ ] Implement alarm playback:
  - Use `afplay` to play alarm sound
  - Loop alarm until stopped
- [ ] Create alarm control functions:
  - `trigger_alarm()` - Start alarm
  - `stop_alarm()` - Stop alarm
- [ ] Manage alarm process lifecycle

### Phase 6: Web UI
- [ ] Create `templates/index.html`:
  - ARM button
  - STOP button
  - Status display
  - Visual feedback (colors, icons)
- [ ] Create `static/css/style.css`:
  - Modern, clean design
  - Responsive layout
  - Status indicators
- [ ] Create `static/js/app.js`:
  - API calls to Flask endpoints
  - Status polling/updates
  - Button event handlers
  - User feedback (alerts, status changes)

### Phase 7: Integration & Testing
- [ ] Integrate all components
- [ ] Test ARM flow:
  - Click ARM → verify caffeinate starts → verify monitoring starts
- [ ] Test alarm trigger:
  - Close lid → verify alarm plays → verify volume maxed
- [ ] Test STOP flow:
  - Click STOP → verify alarm stops → verify caffeinate stops
- [ ] Test edge cases:
  - Multiple ARM clicks
  - App exit while armed
  - Network errors
  - Permission issues

### Phase 8: Polish & Documentation
- [ ] Add error handling and logging
- [ ] Add alarm sound file (or provide instructions)
- [ ] Update README with:
  - Installation instructions
  - Usage guide
  - Requirements (macOS, Python version)
  - Troubleshooting
- [ ] Add comments and docstrings
- [ ] Test on different macOS versions if possible

---

## Technical Details

### macOS Commands Used

1. **`pmset -g log`**
   - Monitors power management events
   - Look for: "clamshell", "sleep", "wake"
   - May need to parse timestamps and filter recent events

2. **`caffeinate -d`**
   - Prevents display sleep (`-d` flag)
   - Can use `-i` to prevent idle sleep, or `-m` for disk sleep
   - Consider `-d -i` for full protection

3. **`osascript -e "set volume output volume 100"`**
   - Sets system volume to maximum
   - Alternative: `osascript -e "set volume 10"` (0-10 scale)

4. **`afplay <sound_file>`**
   - Plays audio file
   - Can loop with `-l` flag or handle looping in code

### Power Event Detection Strategy

**Option A: Polling `pmset -g log`**
- Run `pmset -g log` periodically (every 1-2 seconds)
- Parse output for recent clamshell/sleep events
- Compare timestamps to detect new events

**Option B: Stream `pmset -g logstream`**
- Use `pmset -g logstream` for real-time events
- Parse streaming output
- More efficient but may require different parsing

**Recommended: Start with Option A (polling) for simplicity**

### Alarm Sound
- Provide a loud, attention-grabbing sound file
- Consider multiple formats (mp3, wav, aiff)
- Ensure file is included in project or provide download link

---

## Security & Permissions Considerations

- **No special permissions required** (unlike motion sensors)
- Uses standard macOS utilities available to all users
- Runs entirely locally (no network exposure)
- Consider adding authentication if exposing to network (not needed for localhost-only)

---

## Error Handling

- Handle cases where:
  - `pmset` command fails
  - `caffeinate` process fails to start
  - Alarm sound file missing
  - Volume control fails
  - Thread/process cleanup on exit
  - User closes browser while armed

---

## Future Enhancements (Optional)

- [ ] Configurable alarm sound
- [ ] Adjustable volume level
- [ ] Logging of alarm events
- [ ] Auto-disarm timer
- [ ] Multiple alarm sounds
- [ ] Visual alarm (screen flash)
- [ ] Notification center alerts
- [ ] Password protection for STOP
- [ ] System tray icon
- [ ] Startup on login option

---

## Testing Checklist

- [ ] ARM button arms the system
- [ ] STOP button disarms the system
- [ ] Status updates correctly
- [ ] Caffeinate starts when armed
- [ ] Caffeinate stops when disarmed
- [ ] Closing lid triggers alarm
- [ ] Alarm plays at max volume
- [ ] Alarm stops when STOP clicked
- [ ] Multiple ARM clicks handled gracefully
- [ ] App cleanup on exit
- [ ] Works after system wake
- [ ] Handles missing alarm file gracefully

---

## Dependencies

- **Python 3.7+**
- **Flask** (web framework)
- **macOS** (required for pmset, caffeinate, afplay, osascript)

---

## Notes

- This app must run on macOS (Apple Silicon or Intel)
- Requires Python 3
- No external network dependencies
- All functionality uses built-in macOS utilities
- Consider adding a simple config file for paths/settings

