from flask import Flask, render_template, jsonify, request
import subprocess
import atexit
import os

app = Flask(__name__)

armed = False
caffeinate_process = None

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

def cleanup_on_exit():
    """Cleanup function called when app exits"""
    stop_caffeinate()

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
    return jsonify({
        'status': 'disarmed',
        'armed': False
    })

if __name__ == '__main__': 
    app.run(debug=True, host='127.0.0.1', port=5000)