// function to update the status display
function updateStatus() {
    fetch('/api/status')
    .then(response => response.json())
    .then(data => {
        updateUI(data.armed);
    })
    .catch(error => {
        console.error('Error fetching status:', error);
    });
}

// function to update UI based on armed state
function updateUI(armed) {
    const armOption = document.getElementById('armOption');
    const disarmOption = document.getElementById('disarmOption');
    const statusIndicator = document.getElementById('statusIndicator');
    const indicatorDot = document.getElementById('indicatorDot');
    const indicatorText = document.getElementById('indicatorText');
    
    if (armed) {
        // ARM is active
        armOption.classList.add('active');
        disarmOption.classList.remove('active');
        statusIndicator.classList.remove('disarmed');
        statusIndicator.classList.add('armed');
        indicatorText.textContent = 'ARMED';
    } else {
        // DISARM is active
        disarmOption.classList.add('active');
        armOption.classList.remove('active');
        statusIndicator.classList.remove('armed');
        statusIndicator.classList.add('disarmed');
        indicatorText.textContent = 'DISARMED';
    }
}

// function to arm the system
function arm() {
    // Optimistic UI update - update immediately for instant feedback
    updateUI(true);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // Reduced timeout
    
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
        // Sync with server (in case of any discrepancy)
        updateStatus();
    })
    .catch(error => {
        clearTimeout(timeoutId);
        console.error('Error arming system:', error);
        // Revert UI on error
        updateUI(false);
        updateStatus(); // Sync with actual server state
        if (error.name !== 'AbortError') {
            alert('Failed to arm system: ' + error.message);
        }
    });
}

// function to disarm the system
function disarm() {
    // Optimistic UI update - update immediately for instant feedback
    updateUI(false);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // Reduced timeout
    
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
        // Sync with server (in case of any discrepancy)
        updateStatus();
    })
    .catch(error => {
        clearTimeout(timeoutId);
        console.error('Error disarming system', error);
        // Revert UI on error
        updateUI(true);
        updateStatus(); // Sync with actual server state
        if (error.name !== 'AbortError') {
            alert('Failed to disarm system: ' + error.message);
        }
    });
}

// Initialize on page load
updateStatus();
// Reduce polling frequency to every 3 seconds (less frequent updates)
setInterval(updateStatus, 3000);
