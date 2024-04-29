var pc = null;
var audioStream = null;

// Function to initialize the WebRTC connection

var aiResponse = ""


function selectMicrosoftZiraVoice() {
    const voices = speechSynthesis.getVoices();
    const ziraVoice = voices.find(voice => voice.name.includes("Microsoft Zira"));
    return ziraVoice || voices[0];
}

function textToSpeech(text) {
    if (audioStream) {
        audioStream.getTracks().forEach(track => track.enabled = false);
    }

    var utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.voice = selectMicrosoftZiraVoice();
    utterance.onend = function () {
        console.log('Speech synthesis finished.');

        // Resume the audio stream
        if (audioStream) {
            audioStream.getTracks().forEach(track => track.enabled = true);
        }
    };
    window.speechSynthesis.speak(utterance);
}

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

    dataChannel = pc.createDataChannel("chat");

    // Setup data channel event listeners
    dataChannel.onopen = function(event) {
        console.log("Data channel is open");
    };

    dataChannel.sendOfferToServer = function(offer, dataChannel) {
        console.log("data channal offer to the server");
        console.log(offer);
        console.log(dataChannel);
        dataChannel.send(offer);
    };

    dataChannel.onerror = function(event) {
        console.log("Data channel error:", event);
    };


    dataChannel.onmessage = function(event) {
        aiResponse = event.data;
        textToSpeech(aiResponse);

        console.log("Received message:", event.data);
    };

    dataChannel.onclose = function() {
        console.log("Data channel is closed");
    };

    // Get user media (audio) when the "start" button is clicked
    document.getElementById('start').addEventListener('click', startAudioStreaming);
}

// Function to start audio streaming to the backend
function startAudioStreaming() {
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
    console.log("Sending offer to the server");
    var serverUrl = 'http://localhost:8080/offer';

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
        console.log("answer no one asked");
        console.log(answer);
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
    if (dataChannel) {
        dataChannel.close();
        dataChannel = null;
    }
}

// Initialize the WebRTC connection when the page is loaded
document.addEventListener('DOMContentLoaded', initializeWebRTC);
// Attach event listener to stop button
document.getElementById('stop').addEventListener('click', stopWebRTC);
