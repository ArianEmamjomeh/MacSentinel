from flask import Flask, render_template, jsonify, request
import subprocess
import atexit
import os
import threading
import time


app = Flask(__name__)

armed = False
caffeinate_process = None
alarm_process = None
monitor_thread = None
monitor_running = False

@app.after_request
def after_request(response):
    # Add headers to prevent caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def start_caffeinate():
    """Start caffeinate to prevent system sleep"""
    global caffeinate_process
    stop_caffeinate()

    try:
        caffeinate_process = subprocess.Popen(
            ['caffeinate', '-d', '-i'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"Caffeinate started (PID: {caffeinate_process.pid})")
        return True
    except Exception as e:
        print(f"Error starting caffeinate: {e}")
        caffeinate_process = None
        return False

def stop_caffeinate():
    """Stop caffeinate process"""
    global caffeinate_process

    if caffeinate_process is not None:
        try:
            caffeinate_process.terminate()
            caffeinate_process.wait(timeout=5)
            print(f"Caffeinate stopped (PID: {caffeinate_process.pid})")
        except subprocess.TimeoutExpired:
            caffeinate_process.kill()
            print("Caffeinate force killed")
        except Exception as e:
            print(f"Error stopping caffeinate: {e}")
        finally:
            caffeinate_process = None


def set_volume_max():
    """Set System volume to maximum"""
    try:
        subprocess.run(
            ['osascript', '-e', 'set volume output volume 100'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        print("Volume set to max")
        return True
    except Exception as e:
        print(f"Error setting volume: {e}")
        return False

def trigger_alarm():
    """Start playing alarm sound at maximum volume"""
    global alarm_process
    stop_alarm()
    set_volume_max()
    alarm_sound = os.path.join('static', 'sounds', 'alarm.mp3')
    if not os.path.exists(alarm_sound):
        print(f"Alarm sound file not found: {alarm_sound}")
        return False
    try:
        alarm_process = subprocess.Popen(
            ['afplay', '-l', '999999', alarm_sound],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"Alarm started (PID: {alarm_process.pid})")
        return True
    except Exception as e:
        print(f"Error starting alarm: {e}")
        alarm_process = None
        return False

def stop_alarm():
    """Stop playing alarm sound"""
    global alarm_process
    
    if alarm_process is not None:
        try:
            alarm_process.terminate()
            alarm_process.wait(timeout=2)
            print(f"Alarm stopped (PID: {alarm_process.pid})")
        except subprocess.TimeoutExpired:
            alarm_process.kill()
            print("Alarm force killed")
        except Exception as e:
            print(f"Error stopping alarm: {e}")
        finally:
            alarm_process = None


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
            return []

        lines = result.stdout.strip().split('\n')
        return lines[-20:] if len(lines) > 20 else lines
    except Exception as e:
        print(f"Error reading pmset log: {e}")
        return []

def check_for_lid_close_event(log_lines):
    """check if log contains clamshell close or sleep events"""
    for line in log_lines:
        line_lower = line.lower()
        if 'clamshell' in line_lower and ('close' in line_lower or 'closed' in line_lower):
            return True
        if 'sleep' in line_lower and ('requested' in line_lower or 'entering' in line_lower):
            return True
    return False

def power_monitor_loop():
    """Background thread that monitors power events"""
    global monitor_running, armed
    last_log_count = 0

    while monitor_running:
        try:
            log_lines = parse_pmset_log()
            current_log_count = len(log_lines)

            if current_log_count > last_log_count:
                if armed and check_for_lid_close_event(log_lines):
                    print("LID CLOSE DETECTED")
                    trigger_alarm()
            
            last_log_count = current_log_count

            time.sleep(1)

        except Exception as e:
            print(f"Error in power monitor loop: {e}")
            time.sleep(2)

def start_power_monitoring():
    """Start the power monitoring thread"""
    global monitor_thread, monitor_running

    stop_power_monitoring()

    monitor_running = True
    monitor_thread = threading.Thread(target=power_monitor_loop, daemon=True)
    monitor_thread.start()
    print("Power monitoring started")

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
    stop_caffeinate()
    stop_alarm()
    stop_power_monitoring()

atexit.register(cleanup_on_exit)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return jsonify({'armed': armed})

@app.route('/api/arm', methods=['POST'])
def arm():
    global armed
    armed = True
    caffeinate_started = start_caffeinate()
    start_power_monitoring()
    return jsonify({
        'status': 'armed', 
        'armed': True,
        'caffeinate_started': caffeinate_started
    })

@app.route('/api/stop', methods=['POST'])
def stop():
    global armed
    armed = False
    stop_caffeinate()
    stop_alarm()
    stop_power_monitoring()
    return jsonify({
        'status': 'disarmed',
        'armed': False
    })


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