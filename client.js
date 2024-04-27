var pc = null;
var audioStream = null;

// Function to initialize the WebRTC connection
function initializeWebRTC() {
    // Create the peer connection
    pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.miwifi.com:3478' }]
    });

    // Handle ICE candidates
    pc.onicecandidate = event => {
        console.log("Ice candidate called")
        console.log(event.candidate);
        if (event.candidate === null) {
            console.log("Ice candidate null");
            // Send the offer to the backend when ICE gathering is complete
            sendOfferToServer();
        }
    };

    // Get user media (audio) when the "start" button is clicked
    document.getElementById('start').addEventListener('click', startAudioStreaming);
}

// Function to start audio streaming to the backend
function startAudioStreaming() {
    var serverUrl = 'http://localhost:8999/offer';

    // Get user media (audio)
    navigator.mediaDevices.getUserMedia({ audio: true, video: false })
        .then(stream => {
            audioStream = stream;
            // Add stream tracks to the connection
            stream.getTracks().forEach(track => pc.addTrack(track, stream));

            // Create an offer
            return pc.createOffer();
        })
        .then(offer => pc.setLocalDescription(offer))
        .catch(error => console.error('Error setting up media:', error));
}

// Function to send the offer to the backend
function sendOfferToServer() {
    var serverUrl = 'http://localhost:8999/offer';

    fetch(serverUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            sdp: pc.localDescription.sdp,
            type: pc.localDescription.type
        })
    })
    .then(response => response.json())
    .then(answer => {
        // Set remote description with the answer received from the server
        pc.setRemoteDescription(new RTCSessionDescription(answer));
    })
    .catch(error => console.error('Error sending offer to server:', error));
}

// Function to stop the WebRTC connection
function stopWebRTC() {
    if (pc) {
        pc.close();
        pc = null;
        console.log('WebRTC connection closed.');
    }
    if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
        audioStream = null;
    }
}

// Initialize the WebRTC connection when the page is loaded
document.addEventListener('DOMContentLoaded', initializeWebRTC);
// Attach event listener to stop button
document.getElementById('stop').addEventListener('click', stopWebRTC);
