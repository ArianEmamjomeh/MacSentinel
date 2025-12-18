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
    fetch('/api/arm', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => { 
        console.log('System armed:', data);
        updateStatus();
    })
    .catch(error => {
        console.error('Error arming system:', error);
        alert('Failed to arm system');
    });
}

// function to disarm the system
function stop() {
    fetch('/api/stop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('System disarmed:', data);
        updateStatus();
    })
    .catch(error => {
        console.error('Error disarming system', error);
        alert('Failed to disarm system');
    });
}

updateStatus();
setInterval(updateStatus, 2000);
