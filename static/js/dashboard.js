// Global variables
let cameras = [];
let cameraList = []; // This will store our camera data
let currentToken = '{{token}}';

// Navigation functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize navigation
    const navLinks = document.querySelectorAll('.nav-link');
    const pages = document.querySelectorAll('.page');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetPage = this.getAttribute('data-page');

            // Remove active class from all nav items
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });

            // Add active class to clicked nav item
            this.parentElement.classList.add('active');

            // Hide all pages
            pages.forEach(page => {
                page.classList.remove('active');
            });

            // Show target page
            const targetPageElement = document.getElementById(targetPage + '-page');
            if (targetPageElement) {
                targetPageElement.classList.add('active');

                // Load cameras when camera page is opened
                if (targetPage === 'camera') {
                    loadCameras();
                }
            }
        });
    });

    // Load cameras on initial load if camera page is active
    if (document.getElementById('camera-page') && document.getElementById('camera-page').classList.contains('active')) {
        loadCameras();
    }

    // Initialize chart
    initializeChart();
});

// FIXED: Function to load cameras from API and populate cameraList
async function loadCameras() {
    // First check if we're on the camera page
    const cameraPage = document.getElementById('camera-page');
    if (!cameraPage || !cameraPage.classList.contains('active')) {
        return; // Exit if not on camera page
    }

    const loadingElement = document.getElementById('camera-loading');
    const errorElement = document.getElementById('camera-error');
    const gridContainer = document.getElementById('camera-grid-container');

    // Add null checks for safety
    if (!loadingElement || !errorElement || !gridContainer) {
        console.error('Required elements not found');
        return;
    }

    // Show loading
    loadingElement.style.display = 'block';
    errorElement.style.display = 'none';

    try {
        gridContainer.innerHTML = ''; // Now safe to access

        console.log('🔄 Loading cameras from API...');
        const response = await fetch('/api/cameras', {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const fetchedCameras = await response.json();

        // FIXED: Properly assign to global cameraList
        cameraList = fetchedCameras;
        cameras = fetchedCameras; // Also update the cameras variable for backward compatibility

        console.log('✅ Cameras loaded successfully:', cameraList.length, 'cameras found');
        console.log('📋 Camera data:', cameraList);

        displayCamerasByRoom(cameraList);
        updateEventLog(cameraList);

    } catch (error) {
        console.error('❌ Error loading cameras:', error);
        cameraList = []; // Reset on error
        cameras = [];

        if (errorElement) {
            errorElement.innerHTML = `Error loading cameras: ${error.message}`;
            errorElement.style.display = 'block';
        }

        if (gridContainer) {
            gridContainer.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Unable to load cameras</p>
                    <button class="btn btn-primary" onclick="loadCameras()">Retry</button>
                </div>
            `;
        }
    } finally {
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
}

// Updated function to display cameras in 2-column rows grouped by room
function displayCamerasByRoom(cameras) {
    const gridContainer = document.getElementById('camera-grid-container');

    if (!gridContainer) {
        console.error('Grid container not found');
        return;
    }

    gridContainer.innerHTML = '';

    if (!cameras || cameras.length === 0) {
        gridContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-video-slash"></i>
                <p>No cameras found. Add a camera to get started.</p>
                <button class="btn btn-primary" onclick="loadCameras()">Refresh</button>
            </div>
        `;
        return;
    }

    // Group cameras by room
    const rooms = {};
    cameras.forEach(camera => {
        const room = camera.roomName || 'Unassigned';
        if (!rooms[room]) rooms[room] = [];
        rooms[room].push(camera);
    });

    // Create room sections
    Object.keys(rooms).forEach(roomName => {
        const roomSection = document.createElement('div');
        roomSection.className = 'room-section';

        // Add room title
        const roomTitle = document.createElement('h3');
        roomTitle.className = 'room-title';
        roomTitle.textContent = roomName;
        roomSection.appendChild(roomTitle);

        // Create camera grid for this room
        const cameraGrid = document.createElement('div');
        cameraGrid.className = 'camera-grid';

        // Add all cameras for this room (they'll auto-wrap in rows of 2)
        rooms[roomName].forEach(camera => {
            cameraGrid.appendChild(createCameraCard(camera));
        });

        roomSection.appendChild(cameraGrid);
        gridContainer.appendChild(roomSection);
    });
}

// Helper function to create a camera card
function createCameraCard(camera) {
    const isOnline = camera.status === 'Active';
    const card = document.createElement('div');
    card.className = 'camera-card';

    card.innerHTML = `
        <div class="camera-header">
            <h4>${camera.name || `Camera ${camera.id}`}</h4>
            <span class="status-badge ${isOnline ? 'online' : 'offline'}">
                ${isOnline ? 'Online' : 'Offline'}
            </span>
        </div>
        <div class="camera-info">
            <p><strong>Name:</strong> ${camera.name || 'N/A'}</p>
            <p><strong>MAC:</strong> ${camera.mac || 'N/A'}</p>
            <p><strong>Type:</strong> ${camera.type || 'ipcam'}</p>
            <p><strong>Room:</strong> ${camera.roomName || 'N/A'}</p>
        </div>
        <div class="camera-controls">
            <button class="btn btn-sm btn-primary" onclick="testCamera(${camera.id})" title="Test Camera" style="background-color: #4D44B5;">
                <i class="fas fa-play"></i> Test
            </button>
            <button class="btn btn-sm btn-secondary settings-logo" onclick="openCameraSettings(${camera.id})" title="Settings">
                <i class="fas fa-cog"></i>
            </button>
        </div>
    `;

    return card;
}

// Function to update event log
function updateEventLog(cameras) {
    const eventLogBody = document.getElementById('event-log-body');

    if (!eventLogBody) {
        console.warn('Event log body not found');
        return;
    }

    eventLogBody.innerHTML = '';

    if (!cameras || cameras.length === 0) {
        eventLogBody.innerHTML = '<tr><td colspan="4" class="text-center">No cameras available</td></tr>';
        return;
    }

    cameras.forEach((camera) => {
        const event = document.createElement('tr');
        event.innerHTML = `
            <td><strong>${camera.name || `Camera ${camera.id}`}</strong></td>
            <td>${camera.type || 'N/A'}</td>
            <td>${camera.roomName || 'Unknown Room'}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="testCamera(${camera.id})" style="background-color: #4D44B5;">
                    <i class="fas fa-play"></i> Test Camera
                </button>
            </td>
        `;
        eventLogBody.appendChild(event);
    });
}

// FIXED: Updated testCamera function with better error handling
async function testCamera(cameraId) {
    console.log('🎥 Testing camera with ID:', cameraId);
    console.log('📋 Available cameras:', cameraList);

    // Ensure cameraList is populated
    if (!cameraList || cameraList.length === 0) {
        console.warn('⚠️ Camera list is empty, attempting to reload...');
        showLoadingModal('Loading camera data');

        try {
            await loadCameras();
            closeLoadingModal();

            if (!cameraList || cameraList.length === 0) {
                alert('No cameras available. Please add cameras first.');
                return;
            }
        } catch (error) {
            closeLoadingModal();
            alert('Failed to load camera data. Please try again.');
            return;
        }
    }

    // Find the camera
    const camera = cameraList.find(c => c.id == cameraId); // Use == for type flexibility

    if (!camera) {
        console.error('❌ Camera not found with ID:', cameraId);
        console.log('Available camera IDs:', cameraList.map(c => c.id));
        alert('Camera not found. Please refresh the page and try again.');
        return;
    }

    console.log('✅ Found camera:', camera);

    // Show loading modal
    showLoadingModal(camera.name);

    try {
        if (camera.type === 'ipcam') {
            // If we already have a stream URL, use it
            if (camera.stream_url) {
                openCameraModal(camera, camera.stream_url);
                return;
            }

            // Check if MAC address exists
            if (!camera.mac) {
                throw new Error('Camera MAC address not available');
            }

            // Discover IP address from MAC address
            console.log(`🔍 Discovering IP for camera ${camera.name} with MAC: ${camera.mac}`);

            const ipResponse = await fetch('/api/discover-camera-ip', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mac: camera.mac
                })
            });

            const ipData = await ipResponse.json();

            if (!ipData.success) {
                throw new Error(ipData.error || 'Failed to discover camera IP');
            }

            console.log(`✅ Found IP: ${ipData.ip_address}`);

            // Get camera stream URL
            const streamResponse = await fetch('/api/get-camera-stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ip_address: ipData.ip_address,
                    username: camera.username || 'admin',
                    password: camera.password || 'admin'
                })
            });

            const streamData = await streamResponse.json();

            if (!streamData.success) {
                throw new Error(streamData.error || 'Failed to get stream URL');
            }

            console.log(`📹 Stream URL: ${streamData.stream_url}`);

            // Open camera modal with stream
            openCameraModal(camera, streamData.stream_url, ipData.ip_address);

        } else if (camera.type === 'webcam') {
            // Handle webcam
            openWebcamModal(camera);
        } else {
            throw new Error('Unsupported camera type: ' + camera.type);
        }

    } catch (error) {
        console.error('❌ Error testing camera:', error);
        closeLoadingModal();
        alert(`Error opening camera: ${error.message}`);
    }
}

// Function to refresh cameras
function refreshCameras() {
    console.log('🔄 Refreshing cameras...');
    loadCameras();
}

// Rest of your modal functions remain the same...
function showLoadingModal(cameraName) {
    const loadingModal = `
        <div class="modal" id="loadingModal" style="display: block; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1050;">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Loading Camera</h5>
                    </div>
                    <div class="modal-body text-center">
                        <div class="spinner-border" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="mt-3">Discovering ${cameraName}...</p>
                        <small class="text-muted">Searching network for camera...</small>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', loadingModal);
}

function closeLoadingModal() {
    const modal = document.getElementById('loadingModal');
    if (modal) modal.remove();
}

function openCameraModal(camera, streamUrl, ipAddress = null) {
    closeLoadingModal();

    const modalContent = `
        <div class="modal" id="cameraModal" style="display: block; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1050;">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            ${camera.name}
                            ${ipAddress ? `<small class="text-muted ms-2">(${ipAddress})</small>` : ''}
                        </h5>
                        <button type="button" class="btn-close" onclick="closeModal()">×</button>
                    </div>
                    <div class="modal-body text-center">
                        <div class="camera-stream-container">
                            ${generateStreamContent(streamUrl, camera)}
                        </div>
                        <div class="mt-3">
                            <small class="text-muted">
                                MAC: ${camera.mac} |
                                Type: ${camera.type.toUpperCase()}
                                ${ipAddress ? ` | IP: ${ipAddress}` : ''}
                            </small>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" onclick="refreshStream('${streamUrl}')">
                            🔄 Refresh Stream
                        </button>
                        <button type="button" class="btn btn-primary" onclick="openInNewTab('${streamUrl}')">
                            🔗 Open in New Tab
                        </button>
                        <button type="button" class="btn btn-outline-secondary" onclick="closeModal()">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalContent);
}
function closeModal() {
    console.log('🔄 Closing modal...');

    // Close camera modal
    const cameraModal = document.getElementById('cameraModal');
    if (cameraModal) {
        console.log('📹 Closing camera modal');

        // Stop webcam stream if active
        const video = document.getElementById('webcamVideo');
        if (video && video.srcObject) {
            console.log('🛑 Stopping webcam stream');
            const tracks = video.srcObject.getTracks();
            tracks.forEach(track => {
                track.stop();
                console.log('⏹️ Stopped track:', track.kind);
            });
        }

        // Remove modal from DOM
        cameraModal.remove();
    }

    // Close loading modal
    closeLoadingModal();
}

// Close loading modal specifically
function closeLoadingModal() {
    const loadingModal = document.getElementById('loadingModal');
    if (loadingModal) {
        console.log('⏳ Closing loading modal');
        loadingModal.remove();
    }
}
function generateStreamContent(streamUrl, camera) {
    if (streamUrl.includes('rtsp://')) {
        return `
            <div class="alert alert-info">
                <strong>RTSP Stream Detected</strong><br>
                This camera uses RTSP protocol. You may need a specialized player.
                <br><br>
                <strong>Stream URL:</strong> <code>${streamUrl}</code>
                <br><br>
                <button class="btn btn-sm btn-primary" onclick="copyToClipboard('${streamUrl}')">
                    📋 Copy URL
                </button>
            </div>
        `;
    } else {
        return `
            <div style="position: relative;">
                <img id="cameraStream"
                     src="${streamUrl}"
                     style="max-width: 100%; height: auto; border: 1px solid #ddd; max-height: 500px;"
                     onerror="handleStreamError(this, '${camera.name}')"
                     onload="handleStreamLoad(this)">
                <div id="streamError" style="display: none;" class="alert alert-warning mt-3">
                    <strong>Stream Error</strong><br>
                    Unable to load camera stream. This could be due to:
                    <ul class="text-start mt-2 mb-0">
                        <li>Camera is offline</li>
                        <li>Incorrect credentials</li>
                        <li>Network connectivity issues</li>
                        <li>Unsupported stream format</li>
                    </ul>
                    <div class="mt-3">
                        <strong>Stream URL:</strong> <code>${streamUrl}</code>
                    </div>
                </div>
            </div>
        `;
    }
}

function handleStreamError(img, cameraName) {
    console.error(`❌ Failed to load stream for ${cameraName}`);
    img.style.display = 'none';
    const errorDiv = document.getElementById('streamError');
    if (errorDiv) {
        errorDiv.style.display = 'block';
    }
}

function handleStreamLoad(img) {
    console.log('✅ Camera stream loaded successfully');
    const errorDiv = document.getElementById('streamError');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

function refreshStream(streamUrl) {
    const img = document.getElementById('cameraStream');
    if (img) {
        const separator = streamUrl.includes('?') ? '&' : '?';
        img.src = streamUrl + separator + 't=' + new Date().getTime();
    }
}

function openInNewTab(streamUrl) {
    window.open(streamUrl, '_blank');
}

function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            alert('Stream URL copied to clipboard!');
        }).catch(err => {
            console.error('Failed to copy: ', err);
            fallbackCopyTextToClipboard(text);
        });
    } else {
        fallbackCopyTextToClipboard(text);
    }
}

function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.top = '0';
    textArea.style.left = '0';
    textArea.style.width = '2em';
    textArea.style.height = '2em';
    textArea.style.padding = '0';
    textArea.style.border = 'none';
    textArea.style.outline = 'none';
    textArea.style.boxShadow = 'none';
    textArea.style.background = 'transparent';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        document.execCommand('copy');
        alert('Stream URL copied to clipboard!');
    } catch (err) {
        console.error('Fallback: Unable to copy', err);
        alert('Unable to copy to clipboard. URL: ' + text);
    }

    document.body.removeChild(textArea);
}

function openWebcamModal(camera) {
    closeLoadingModal();

    const modalContent = `
        <div class="modal" id="cameraModal" style="display: block; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1050;">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${camera.name} (Webcam)</h5>
                        <button type="button" class="btn-close" onclick="closeModal()">×</button>
                    </div>
                    <div class="modal-body text-center">
                        <video id="webcamVideo" width="640" height="480" autoplay>
                            Your browser does not support the video tag.
                        </video>
                        <div class="mt-3">
                            <small class="text-muted">Device: ${camera.mac}</small>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-outline-secondary" onclick="closeModal()">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalContent);

    initializeWebcam(camera.mac);
}

async function initializeWebcam(deviceId) {
    try {
        console.log(`🎥 Initializing webcam with device ID: ${deviceId}`);

        // Check if this is a V4L device path
        if (typeof deviceId === 'string' && deviceId.includes('/dev/v4l/by-id/')) {
            await initializeServerWebcam(deviceId);
            return;
        }

        // Browser-based webcam initialization
        let actualDeviceId = deviceId;

        // Get available video devices first
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(device => device.kind === 'videoinput');

        console.log('📱 Available video devices:', videoDevices);

        let constraints = { video: true };

        // Try to match device by label or deviceId
        if (actualDeviceId && actualDeviceId !== 'undefined') {
            const matchingDevice = videoDevices.find(device =>
                device.deviceId === actualDeviceId ||
                device.label.toLowerCase().includes(actualDeviceId.toLowerCase())
            );

            if (matchingDevice) {
                constraints = {
                    video: {
                        deviceId: { exact: matchingDevice.deviceId },
                        width: { ideal: 640 },
                        height: { ideal: 480 }
                    }
                };
                console.log(`✅ Found matching device: ${matchingDevice.label}`);
            } else {
                console.warn(`⚠️ No matching device found for: ${actualDeviceId}, using default`);
            }
        }

        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        const video = document.getElementById('webcamVideo');

        if (video) {
            video.srcObject = stream;

            // Add stream info to modal
            const usedDevice = videoDevices.find(device =>
                stream.getVideoTracks()[0].getSettings().deviceId === device.deviceId
            );

            if (usedDevice) {
                updateWebcamInfo(usedDevice);
            }
        }

    } catch (error) {
        console.error('❌ Error accessing webcam:', error);

        // Show detailed error message
        const errorMessage = getWebcamErrorMessage(error);
        showWebcamError(errorMessage);
    }
}

async function initializeServerWebcam(devicePath) {
    try {
        // Extract camera name from V4L path
        const cameraName = devicePath.split('/').pop();
        console.log(`🔌 Initializing server webcam: ${cameraName}`);

        // Test webcam accessibility first
        const testResponse = await fetch(`/api/webcam/test/${cameraName}`);
        const testData = await testResponse.json();

        if (!testData.success) {
            throw new Error(testData.error);
        }

        console.log(`✅ Server webcam test successful:`, testData);

        // Replace video element with img element for server stream
        const video = document.getElementById('webcamVideo');
        if (video) {
            const img = document.createElement('img');
            img.id = 'webcamStream';
            img.src = testData.stream_url;
            img.style.cssText = video.style.cssText;
            img.onerror = () => showWebcamError('Failed to load webcam stream from server');

            video.parentNode.replaceChild(img, video);

            // Update info
            updateWebcamInfo({
                label: `V4L Device: ${cameraName}`,
                deviceId: `Device ${testData.device_num}`
            });
        }

    } catch (error) {
        console.error('❌ Error initializing server webcam:', error);
        showWebcamError(`Server webcam error: ${error.message}`);
    }
}

function getWebcamErrorMessage(error) {
    switch (error.name) {
        case 'NotFoundError':
            return 'No webcam found. Please check if a camera is connected.';
        case 'NotAllowedError':
            return 'Camera access denied. Please allow camera permissions.';
        case 'NotReadableError':
            return 'Camera is already in use by another application.';
        case 'OverconstrainedError':
            return 'Requested camera configuration is not supported.';
        default:
            return `Camera error: ${error.message}`;
    }
}

function showWebcamError(message) {
    const video = document.getElementById('webcamVideo');
    if (video) {
        video.style.display = 'none';
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.innerHTML = `
            <strong>Webcam Error</strong><br>
            ${message}
            <br><br>
            <button class="btn btn-sm btn-primary" onclick="retryWebcam()">
                🔄 Retry
            </button>
        `;
        video.parentNode.insertBefore(errorDiv, video.nextSibling);
    }
}

function updateWebcamInfo(device) {
    const infoElement = document.querySelector('#cameraModal .text-muted');
    if (infoElement) {
        infoElement.innerHTML = `
            Device: ${device.label || 'Unknown Camera'}<br>
            ID: ${device.deviceId}
        `;
    }
}

function retryWebcam() {
    const modal = document.getElementById('cameraModal');
    if (modal) {
        const camera = {
            name: modal.querySelector('.modal-title').textContent.replace(' (Webcam)', ''),
            mac: 'retry' // placeholder
        };
        closeModal();
        setTimeout(() => openWebcamModal(camera), 100);
    }
}

function toggleRecording(cameraId) {
    console.log(`Toggle recording for camera ${cameraId}`);
    // Implement recording toggle logic here
}

function openCameraSettings(cameraId) {
    console.log(`Open settings for camera ${cameraId}`);
    // Implement camera settings modal/page here
}

function initializeChart() {
    const ctx = document.getElementById('attendanceChart');
    if (ctx) {
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Present', 'Absent'],
                datasets: [{
                    data: [142, 8],
                    backgroundColor: ['#10b981', '#ef4444'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
}

// Console welcome message
console.log('%c🎓 Academic Management Dashboard', 'color: #3b82f6; font-size: 16px; font-weight: bold;');
console.log('%cDashboard loaded successfully!', 'color: #22c55e; font-size: 14px;');