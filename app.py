from flask import Flask, render_template, jsonify, request
import subprocess
import atexit
import os
import threading
import time


app = Flask(__name__)

armed = False
alarm_process = None
alarm_loop_thread = None
monitor_thread = None
monitor_running = False

@app.after_request
def after_request(response):
    # Add headers to prevent caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    # Add CORS headers to allow requests from browser
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

def check_external_audio():
    """Check if external audio devices are available"""
    try:
        result = subprocess.run(
            ['system_profiler', 'SPAudioDataType'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=3
        )
        if result.returncode == 0:
            output = result.stdout.lower()
            # Check for external audio devices (Bluetooth, USB, etc.)
            external_keywords = ['bluetooth', 'usb', 'airpods', 'headphones', 'speaker']
            for keyword in external_keywords:
                if keyword in output and 'built-in' not in output.split(keyword)[0][-50:]:
                    print(f"External audio device detected (may work with lid closed)")
        return True
        return False
    except:
        return False

def set_volume_max():
    """Set System volume to maximum and unmute"""
    try:
        # Set volume to max and unmute
        subprocess.run(
            ['osascript', '-e', 'set volume output volume 100 without output muted'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        # Also try the alternative method
        subprocess.run(
            ['osascript', '-e', 'set volume without output muted'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True
    except Exception as e:
        print(f"Error setting volume: {e}")
        return False

def trigger_alarm():
    """Start playing alarm sound at maximum volume"""
    global alarm_process
    stop_alarm()
    set_volume_max()
    
    # Note: macOS disables built-in speakers when lid is closed (hardware limitation)
    # We'll try multiple audio methods, but built-in audio won't work with lid closed
    print("NOTE: macOS disables built-in speakers when lid closes (hardware/OS limitation).")
    print("      Alarm will trigger and attempt to play, but audio requires lid to be open or external audio device.")
    
    # Get absolute path to alarm file - try multiple methods
    base_dir = os.path.dirname(os.path.abspath(__file__))
    alarm_sound = os.path.join(base_dir, 'static', 'sounds', 'alarm.mp3')
    
    # Also try using Flask's static folder
    if not os.path.exists(alarm_sound):
        # Try relative to current working directory
        alarm_sound = os.path.join('static', 'sounds', 'alarm.mp3')
        if not os.path.exists(alarm_sound):
            alarm_sound = os.path.abspath(os.path.join('static', 'sounds', 'alarm.mp3'))
    
    if not os.path.exists(alarm_sound):
        print(f"ERROR: Alarm sound file not found!")
        print(f"  Tried: {os.path.join(base_dir, 'static', 'sounds', 'alarm.mp3')}")
        print(f"  Tried: {os.path.join('static', 'sounds', 'alarm.mp3')}")
        print(f"  Current working directory: {os.getcwd()}")
        print(f"  Base directory: {base_dir}")
        return False
    
    # Make sure it's an absolute path
    alarm_sound = os.path.abspath(alarm_sound)
    print(f"Playing alarm from: {alarm_sound}")
    
    try:
        # Use absolute path - don't capture stdout so sound can play
        # Note: -l flag doesn't exist in this afplay version, so we'll loop manually
        global alarm_loop_thread
        
        # Start playing immediately (first iteration)
        try:
            # Try afplay first
            proc = subprocess.Popen(
                ['afplay', '-v', '1', alarm_sound],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            alarm_process = proc
            print(f"Alarm started (PID: {alarm_process.pid})")
            
            # Also try to use system beep as backup (works even with lid closed on some Macs)
            # This will run in parallel and might work when afplay doesn't
            try:
                beep_proc = subprocess.Popen(
                    ['osascript', '-e', 'beep'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except:
                pass  # Beep is optional
                
        except Exception as e:
            print(f"ERROR: Failed to start alarm process: {e}")
            return False
        
        def play_alarm_loop():
            """Loop the alarm sound until stopped"""
            global alarm_process, armed, monitor_running
            consecutive_failures = 0
            max_failures = 10
            
            while monitor_running and armed:
                try:
                    # Check armed state frequently (don't wait too long)
                    if not armed:
                        break
                    
                    # Wait for current playback to finish, but check armed state periodically
                    if alarm_process:
                        # Use poll() with timeout instead of wait() to check armed state
                        while alarm_process.poll() is None:
                            if not armed:
                                alarm_process.terminate()
                                break
                            time.sleep(0.1)
                    
                    if not (monitor_running and armed):
                        break
                    
                    time.sleep(0.1)  # Brief pause before restarting
                    
                    # Check again before starting new playback
                    if not armed:
                        break
                    
                    # Ensure volume is max before each playback (in case it was lowered)
                    set_volume_max()
                    
                    # Try multiple audio methods in parallel to maximize chance of success
                    # Method 1: afplay (primary)
                    proc = subprocess.Popen(
                        ['afplay', '-v', '1', alarm_sound],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE
                    )
                    
                    # Method 2: System beep (might work differently)
                    try:
                        subprocess.Popen(
                            ['osascript', '-e', 'beep'],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                    except:
                        pass
                    
                    # Method 3: System alert sound (alternative)
                    try:
                        subprocess.Popen(
                            ['osascript', '-e', 'beep 2'],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                    except:
                        pass
                    
                    # Method 4: Try using 'say' command as backup (text-to-speech)
                    # This uses a different audio path that might work
                    try:
                        subprocess.Popen(
                            ['say', '-v', 'Alex', 'alarm'],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                    except:
                        pass
                    
                    # Check if it started successfully
                    time.sleep(0.2)
                    if proc.poll() is None:
                        alarm_process = proc
                        consecutive_failures = 0  # Reset failure counter
                    else:
                        # Playback failed, read error
                        _, stderr_output = proc.communicate()
                        error_msg = stderr_output.decode('utf-8') if stderr_output else "Unknown error"
                        consecutive_failures += 1
                        print(f"Warning: Alarm playback failed (attempt {consecutive_failures}): {error_msg}")
                        
                        if consecutive_failures >= max_failures:
                            print("ERROR: Alarm playback failed too many times, stopping retries")
                            break
                        
                        # Wait longer before retrying after failure
                        time.sleep(1)
                        
                except Exception as e:
                    print(f"Error in alarm loop: {e}")
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        break
                    time.sleep(1)
        
        # Start the looping thread to continue playback
        alarm_loop_thread = threading.Thread(target=play_alarm_loop, daemon=True)
        alarm_loop_thread.start()
        
        return True
    except Exception as e:
        print(f"ERROR: Error starting alarm: {e}")
        import traceback
        traceback.print_exc()
        alarm_process = None
        return False

def stop_alarm():
    """Stop playing alarm sound"""
    global alarm_process, alarm_loop_thread
    
    # Kill the current alarm process
    if alarm_process is not None:
        try:
            alarm_process.terminate()
            alarm_process.wait(timeout=1)
            print(f"Alarm stopped (PID: {alarm_process.pid})")
        except subprocess.TimeoutExpired:
            alarm_process.kill()
            print("Alarm force killed")
        except Exception as e:
            print(f"Error stopping alarm process: {e}")
        finally:
            alarm_process = None
    
    # Kill all afplay processes (in case multiple are running)
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'afplay.*alarm.mp3'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    try:
                        os.kill(int(pid), 15)  # SIGTERM
                        print(f"Killed afplay process (PID: {pid})")
                    except:
                        pass
    except Exception as e:
        print(f"Error killing afplay processes: {e}")
    
    # The loop thread will exit when armed becomes False (already set above)
    # Give it a moment to exit
    if alarm_loop_thread is not None and alarm_loop_thread.is_alive():
        import time
        time.sleep(0.2)  # Brief wait for thread to exit
        if alarm_loop_thread.is_alive():
            print("Warning: Alarm loop thread did not exit immediately")
    
    print("Alarm fully stopped")


def parse_pmset_log():
    """Get recent power events from pmset log"""
    try:
        result = subprocess.run(
        ['pmset', '-g', 'log'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, 
        text=True,
        timeout=5
        )

        if result.returncode != 0:
            print(f"pmset command failed with return code {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return []

        lines = result.stdout.strip().split('\n')
        # Get more lines to catch events that might have happened
        recent_lines = lines[-50:] if len(lines) > 50 else lines
        return recent_lines
    except Exception as e:
        print(f"Error reading pmset log: {e}")
        return []

def check_for_lid_close_event(log_lines):
    """check if log contains clamshell close or sleep events"""
    for line in log_lines:
        line_lower = line.lower()
        # Check for clamshell close events (various patterns)
        if 'clamshell' in line_lower:
            if any(keyword in line_lower for keyword in ['close', 'closed', 'closing']):
                if 'open' not in line_lower and 'wake' not in line_lower:
                    print(f"Detected clamshell close: {line[:100]}")
                    return True
        # Check for display sleep (which happens when lid closes)
        if 'display' in line_lower and 'sleep' in line_lower:
            if 'wake' not in line_lower and 'woke' not in line_lower and 'waking' not in line_lower:
                print(f"Detected display sleep: {line[:100]}")
                return True
        # Check for lid-related events
        if 'lid' in line_lower and ('close' in line_lower or 'closed' in line_lower):
            if 'open' not in line_lower and 'wake' not in line_lower:
                print(f"Detected lid close: {line[:100]}")
                return True
    return False

def check_lid_state():
    """Check current lid state using ioreg"""
    try:
        result = subprocess.run(
            ['ioreg', '-r', '-k', 'AppleClamshellState'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=0.5  # Faster timeout for more frequent checks
        )
        if result.returncode == 0:
            # Look for AppleClamshellState
            for line in result.stdout.split('\n'):
                if 'AppleClamshellState' in line:
                    # Check various formats: "= Yes", "= 1", "= No", "= 0"
                    line_lower = line.lower()
                    if '= yes' in line_lower or '= 1' in line_lower:
                        return True  # Lid is closed
                    elif '= no' in line_lower or '= 0' in line_lower:
                        return False  # Lid is open
        return None  # Couldn't determine
    except subprocess.TimeoutExpired:
        # Timeout is okay, just return None
        return None
    except Exception as e:
        # If ioreg fails, return None to indicate we can't check
        return None

def power_monitor_loop():
    """Background thread that monitors power events"""
    global monitor_running, armed
    last_lid_state = None
    initialized = False

    while monitor_running:
        try:
            # Check lid state directly
            lid_state = check_lid_state()
            
            if lid_state is not None:
                # On first check after arming, initialize the lid state
                # This ensures we only trigger on transitions AFTER arming
                if not initialized:
                    last_lid_state = lid_state
                    initialized = True
                    print(f"Monitoring initialized - lid is currently {'CLOSED' if lid_state else 'OPEN'}")
                else:
                    # Only trigger if lid transitions from OPEN to CLOSED
                    # This ensures we only detect actual lid close events, not just the lid being closed
                    if lid_state and last_lid_state is False and armed:
                        print("LID CLOSE DETECTED - TRIGGERING ALARM")
                        trigger_alarm()
                    last_lid_state = lid_state
            
            time.sleep(0.5)  # Check more frequently for better responsiveness

        except Exception as e:
            print(f"Error in power monitor loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(2)

def start_power_monitoring():
    """Start the power monitoring thread"""
    global monitor_thread, monitor_running

    stop_power_monitoring()
    
    # Reset any alarm trigger state when starting fresh
    print("Starting fresh power monitoring session")

    # Verify pmset command works (with shorter timeout to avoid blocking)
    try:
        test_result = subprocess.run(
            ['pmset', '-g', 'log'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=1  # Reduced timeout
        )
        if test_result.returncode != 0:
            print(f"WARNING: pmset command may not be working (return code: {test_result.returncode})")
    except subprocess.TimeoutExpired:
        print("WARNING: pmset command timed out during test (will continue anyway)")
    except Exception as e:
        print(f"WARNING: Could not test pmset command: {e}")

    monitor_running = True
    monitor_thread = threading.Thread(target=power_monitor_loop, daemon=True)
    monitor_thread.start()
    print("Power monitoring started - watching for lid close events")

def stop_power_monitoring():
    """Stop the power monitoring thread"""
    global monitor_thread, monitor_running

    monitor_running = False

    if monitor_thread is not None:
        monitor_thread.join(timeout=2)
        monitor_thread = None
        print("Power monitoring stopped")


def cleanup_on_exit():
    """Cleanup function called when app exits"""
    stop_alarm()
    stop_power_monitoring()

atexit.register(cleanup_on_exit)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return jsonify({'armed': armed})

def _arm_background():
    """Background function to start power monitoring"""
    try:
        start_power_monitoring()
    except Exception as e:
        print(f"Error in background arm setup: {e}")
        import traceback
        traceback.print_exc()

@app.route('/api/arm', methods=['POST', 'OPTIONS'])
def arm():
    if request.method == 'OPTIONS':
        return '', 200
    
    global armed
    try:
        armed = True
        # Start setup in background thread to respond immediately
        setup_thread = threading.Thread(target=_arm_background, daemon=True)
        setup_thread.start()
        
        # Respond immediately without waiting for setup
        return jsonify({
            'status': 'armed', 
            'armed': True
        })
    except Exception as e:
        print(f"Error in /api/arm: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'armed': False,
            'error': str(e)
        }), 500

@app.route('/api/stop', methods=['POST', 'OPTIONS'])
def stop():
    if request.method == 'OPTIONS':
        return '', 200
    
    global armed
    try:
        # Set armed to False FIRST so alarm loop thread will exit
        armed = False
        # Give a brief moment for the loop to see the change
        time.sleep(0.1)
        
        stop_alarm()
        stop_power_monitoring()
        
        # Reset alarm trigger state when disarming
        print("System disarmed - resetting all detection states")
        
        return jsonify({
            'status': 'disarmed',
            'armed': False
        })
    except Exception as e:
        print(f"Error in /api/stop: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'armed': False,
            'error': str(e)
        }), 500


@app.route('/api/test-alarm', methods=['POST'])
def test_alarm():
    """Test endpoint to manually trigger alarm"""
    success = trigger_alarm()
    return jsonify({
        'status': 'alarm_triggered' if success else 'alarm_failed',
        'success': success
    })



if __name__ == '__main__': 
    app.run(debug=True, host='127.0.0.1', port=5000)