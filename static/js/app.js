// function to update the status display
function updateStatus() {
    fetch('/api/status')
    .then(response => response.json())
    .then(data => {
        const statusElement = document.getElementById('status');
        if (data.armed) {
            statusElement.textContent = 'ARMED';
            statusElement.className = 'status armed';
        } else {
            statusElement.textContent = 'DISARMED';
            statusElement.className = 'status disarmed';
        }
    })
    .catch(error => {
        console.error('Error Fetching status:', error);
    });
}

// function to arm the system
function arm() {
    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
    
    fetch('/api/arm', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        signal: controller.signal
    })
    .then(response => {
        clearTimeout(timeoutId);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => { 
        console.log('System armed:', data);
        updateStatus();
    })
    .catch(error => {
        clearTimeout(timeoutId);
        console.error('Error arming system:', error);
        if (error.name === 'AbortError') {
            alert('Request timed out. Please try again.');
        } else {
            alert('Failed to arm system: ' + error.message);
        }
    });
}

// function to disarm the system
function stop() {
    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
    
    fetch('/api/stop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        signal: controller.signal
    })
    .then(response => {
        clearTimeout(timeoutId);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('System disarmed:', data);
        updateStatus();
    })
    .catch(error => {
        clearTimeout(timeoutId);
        console.error('Error disarming system', error);
        if (error.name === 'AbortError') {
            alert('Request timed out. Please try again.');
        } else {
            alert('Failed to disarm system: ' + error.message);
        }
    });
}

// function to test alarm
function testAlarm() {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    
    fetch('/api/test-alarm', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        signal: controller.signal
    })
    .then(response => {
        clearTimeout(timeoutId);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Test alarm:', data);
        if (data.success) {
            alert('Alarm test triggered! You should hear the alarm sound.');
        } else {
            alert('Alarm test failed. Check console for details.');
        }
    })
    .catch(error => {
        clearTimeout(timeoutId);
        console.error('Error testing alarm:', error);
        alert('Failed to test alarm: ' + error.message);
    });
}

updateStatus();
setInterval(updateStatus, 2000);
