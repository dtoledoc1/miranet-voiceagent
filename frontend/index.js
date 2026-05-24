// WebSocket & Audio State Variables
let socket = null;
let audioContext = null;
let mediaStream = null;
let scriptProcessor = null;
let analyserNode = null;
let isListening = false;
let sessionID = '';

// Web Speech API Recognition Variables
let recognition = null;
let transcribedText = '';

// Canvas Visualizer Variables
const canvas = document.getElementById('waveform-canvas');
const ctx = canvas.getContext('2d');
let animationFrameId = null;

// DOM Elements
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const micToggleBtn = document.getElementById('mic-toggle-btn');
const micBtnLabel = document.getElementById('mic-btn-label');
const processVoiceBtn = document.getElementById('speech-trigger-btn');
const reconnectBtn = document.getElementById('reconnect-server-btn');
const chatLog = document.getElementById('chat-log-container');
const ttsToggle = document.getElementById('tts-toggle');
const overlayText = document.getElementById('visualizer-overlay-text');
const textQueryInput = document.getElementById('text-query-input');
const sendQueryBtn = document.getElementById('send-query-btn');

// Metadata Nodes
const metaWhisper = document.getElementById('meta-whisper');
const metaOllama = document.getElementById('meta-ollama');
const metaDB = document.getElementById('meta-db');
const metaSession = document.getElementById('meta-session');

const valLatency = document.getElementById('val-latency');
const valJitter = document.getElementById('val-jitter');
const valLoss = document.getElementById('val-loss');
const valBandwidth = document.getElementById('val-bandwidth');

// Initialize Dashboard
window.addEventListener('DOMContentLoaded', () => {
    // Generate unique session ID
    sessionID = 'session_' + Math.random().toString(36).substring(2, 10);
    metaSession.textContent = sessionID;

    // Set canvas resolution
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Initial canvas render (idle flat line)
    drawWaveform();

    // Connect to WebSocket Server
    connectWebSocket();

    // Initialize Web Speech API Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'es-ES'; // Set Spanish recognition

        recognition.onresult = (event) => {
            let interimTranscript = "";
            let finalTranscript = "";

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            // Accumulate transcribed text
            const newText = finalTranscript || interimTranscript;
            if (newText.trim()) {
                transcribedText = newText;
                console.log(`Speech Recognition result: ${transcribedText}`);
                overlayText.textContent = `Escuchado: "${transcribedText}"`;
            }
        };

        recognition.onerror = (event) => {
            console.error("Speech recognition error:", event.error);
            if (event.error === 'not-allowed') {
                overlayText.textContent = "Error: Permiso de voz denegado.";
                overlayText.style.color = "var(--danger-color)";
            }
        };

        recognition.onend = () => {
            console.log("Speech recognition ended.");
            // If the user is still recording, auto-restart the recognition session
            if (isListening) {
                try {
                    recognition.start();
                    console.log("Speech recognition restarted automatically.");
                } catch (e) {
                    console.warn("Failed to restart speech recognition:", e);
                }
            }
        };
    } else {
        console.warn("Speech Recognition API is not supported in this browser.");
    }

    // Setup Button Events
    micToggleBtn.addEventListener('click', toggleListening);
    processVoiceBtn.addEventListener('click', triggerProcessing);
    reconnectBtn.addEventListener('click', () => {
        if (socket) socket.close();
        connectWebSocket();
    });

    // Setup Text Input Events
    sendQueryBtn.addEventListener('click', sendTextInput);
    textQueryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            sendTextInput();
        }
    });
});

function resizeCanvas() {
    canvas.width = canvas.parentElement.clientWidth * window.devicePixelRatio;
    canvas.height = canvas.parentElement.clientHeight * window.devicePixelRatio;
}

// ----------------------------------------------------
// WebSocket Connections & Message Handlers
// ----------------------------------------------------
function connectWebSocket() {
    // Determine ws vs wss, local host vs remote
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.port === '5500' ? 'localhost:8000' : (window.location.host || 'localhost:8000');
    const wsUrl = `${protocol}//${host}/ws/voice?session_id=${sessionID}`;
    
    console.log(`Connecting to WebSocket: ${wsUrl}`);
    statusText.textContent = 'Conectando...';
    statusIndicator.className = 'connection-status-badge';

    socket = new WebSocket(wsUrl);

    socket.onopen = async () => {
        console.log('WebSocket connection established.');
        statusText.textContent = 'Conectado';
        statusIndicator.classList.add('connected');
        reconnectBtn.disabled = true;
        
        // Fetch server model settings
        fetchServerHealth();
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            
            // 1. Live stream metrics reports
            if (data.type === 'network_status') {
                updateMetrics(data.metrics);
            } 
            // 2. Final response output
            else if (data.type === 'agent_response') {
                renderAgentResponse(data);
            }
            // 3. Simple text status logs
            else if (data.type === 'status') {
                console.log(`Server status: ${data.message}`);
            }
            // 4. Server error logs
            else if (data.type === 'error') {
                console.error(`Server error reported: ${data.message}`);
                addSystemMessage(`Error: ${data.message}`);
            }
        } catch (e) {
            console.error('Failed to parse websocket JSON message:', e);
        }
    };

    socket.onclose = () => {
        console.log('WebSocket connection closed.');
        statusText.textContent = 'Desconectado';
        statusIndicator.className = 'connection-status-badge';
        reconnectBtn.disabled = false;
        
        // Disable mic and processing if disconnected
        if (isListening) stopAudioCapture();
        isListening = false;
        updateUIState();
        
        addSystemMessage('Conexión con el servidor finalizada.');
    };

    socket.onerror = (error) => {
        console.error('WebSocket connection error:', error);
    };
}

async function fetchServerHealth() {
    try {
        const protocol = window.location.protocol;
        const host = window.location.port === '5500' ? 'localhost:8000' : (window.location.host || 'localhost:8000');
        const response = await fetch(`${protocol}//${host}/health`);
        const info = await response.json();
        
        if (info.status === 'online') {
            metaWhisper.textContent = info.config.whisper_model;
            metaOllama.textContent = info.config.ollama_model;
            metaDB.textContent = info.database === 'healthy' ? 'Conectado' : 'Sin Persistencia';
            metaDB.style.color = info.database === 'healthy' ? 'var(--success-color)' : 'var(--warning-color)';
        }
    } catch (e) {
        console.error('Failed to retrieve server configurations:', e);
    }
}

// ----------------------------------------------------
// UI Renderers
// ----------------------------------------------------
function updateMetrics(metrics) {
    if (!metrics) return;
    valLatency.innerHTML = `${metrics.latency_ms} <span class="unit">ms</span>`;
    valJitter.innerHTML = `${metrics.jitter_ms} <span class="unit">ms</span>`;
    
    const lossPercentage = (metrics.packet_loss_rate * 100).toFixed(1);
    valLoss.innerHTML = `${lossPercentage} <span class="unit">%</span>`;
    valLoss.style.color = metrics.packet_loss_rate > 0.05 ? 'var(--danger-color)' : 'var(--text-primary)';
    
    valBandwidth.innerHTML = `${metrics.bandwidth_kbps} <span class="unit">kbps</span>`;
}

function addSystemMessage(text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message system-msg';
    msgDiv.innerHTML = `<div class="msg-bubble">${text}</div>`;
    chatLog.appendChild(msgDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
}

function renderAgentResponse(data) {
    // 1. Remove loading indicator if exists
    const loader = document.getElementById('chat-agent-loader');
    if (loader) loader.remove();

    // 2. Append User Speech Bubble
    const userDiv = document.createElement('div');
    userDiv.className = 'chat-message user-msg';
    userDiv.innerHTML = `
        <div class="msg-bubble">${data.transcription}</div>
        <div class="msg-meta">Usuario</div>
    `;
    chatLog.appendChild(userDiv);

    // 3. Append Agent Voice Response Bubble
    const agentDiv = document.createElement('div');
    agentDiv.className = 'chat-message agent-msg';
    agentDiv.innerHTML = `
        <div class="msg-bubble">${data.response}</div>
        <div class="msg-meta">
            <span>Miranet VoiceAgent</span>
            <span class="badge badge-intent">${data.intent}</span>
            <span class="badge badge-sentiment">${data.sentiment}</span>
        </div>
    `;
    chatLog.appendChild(agentDiv);
    chatLog.scrollTop = chatLog.scrollHeight;

    // 4. Play Text-to-Speech if enabled
    if (ttsToggle.checked && data.response) {
        speakResponse(data.response);
    }
}

function renderAgentLoading() {
    const loaderDiv = document.createElement('div');
    loaderDiv.className = 'chat-message agent-msg';
    loaderDiv.id = 'chat-agent-loader';
    loaderDiv.innerHTML = `
        <div class="msg-bubble" style="opacity: 0.6;">Generando respuesta...</div>
        <div class="msg-meta">Procesando Inteligencia Artificial...</div>
    `;
    chatLog.appendChild(loaderDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
}

function speakResponse(text) {
    // Cancel ongoing Speech
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'es-ES'; // Set Spanish accent
    
    // Find local Spanish voice if available
    const voices = window.speechSynthesis.getVoices();
    const esVoice = voices.find(voice => voice.lang.startsWith('es'));
    if (esVoice) utterance.voice = esVoice;
    
    window.speechSynthesis.speak(utterance);
}

// ----------------------------------------------------
// Voice Capture & PCM Resampling Pipeline
// ----------------------------------------------------
async function toggleListening() {
    if (isListening) {
        // Stop recording
        stopAudioCapture();
        isListening = false;
        updateUIState();
    } else {
        // Start recording
        const success = await startAudioCapture();
        if (success) {
            isListening = true;
            updateUIState();
        }
    }
}

async function startAudioCapture() {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        alert('Por favor, establezca conexión con el servidor primero.');
        return false;
    }

    try {
        // Request user microphone
        mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });

        // Initialize Web Audio context
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContext.createMediaStreamSource(mediaStream);

        // Analyser for drawing wave
        analyserNode = audioContext.createAnalyser();
        analyserNode.fftSize = 256;
        source.connect(analyserNode);

        // Set up buffer ScriptProcessor to downsample inline.
        // We use 4096 buffer size.
        scriptProcessor = audioContext.createScriptProcessor(4096, 1, 1);
        source.connect(scriptProcessor);
        scriptProcessor.connect(audioContext.destination);

        const inputSampleRate = audioContext.sampleRate;
        const outputSampleRate = 16000; // Target rate for OpenAI Whisper

        scriptProcessor.onaudioprocess = (audioProcessingEvent) => {
            if (!isListening) return;

            const inputBuffer = audioProcessingEvent.inputBuffer;
            const channelData = inputBuffer.getChannelData(0); // Left channel (mono)

            // 1. Downsample float32 buffer to 16000Hz
            const downsampledData = downsampleBuffer(channelData, inputSampleRate, outputSampleRate);

            // 2. Convert Float32 array [-1.0, 1.0] to Int16 array [-32768, 32767]
            const pcmBuffer = floatTo16BitPCM(downsampledData);

            // 3. Send raw binary PCM ArrayBuffer chunk through WebSocket
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(pcmBuffer);
            }
        };

        overlayText.textContent = "Escuchando... Habla ahora.";
        overlayText.style.color = "var(--primary-color)";
        
        if (recognition) {
            transcribedText = "";
            recognition.start();
            console.log("Speech recognition started.");
        }

        return true;
    } catch (err) {
        console.error('Failed to access microphone:', err);
        alert(`No se pudo acceder al micrófono.\n\nDetalle técnico: ${err.name} - ${err.message}\n\nAsegúrate de dar los permisos necesarios en el candado del navegador.`);
        return false;
    }
}

function stopAudioCapture() {
    if (recognition) {
        recognition.stop();
        console.log("Speech recognition stopped manually.");
    }

    // Give Speech Recognition a small window to resolve the final text
    setTimeout(() => {
        if (transcribedText && transcribedText.trim() !== "") {
            overlayText.textContent = `Texto detectado: "${transcribedText}"`;
            overlayText.style.color = "var(--primary-color)";
        } else {
            overlayText.textContent = "No se detectó voz hablada. Escribe tu queja en la caja de abajo.";
            overlayText.style.color = "var(--warning-color)";
        }
    }, 300);

    if (scriptProcessor) {
        scriptProcessor.disconnect();
        scriptProcessor = null;
    }
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
}

function updateUIState() {
    if (isListening) {
        micToggleBtn.className = 'btn btn-secondary btn-round';
        micBtnLabel.textContent = 'Detener Micrófono';
        processVoiceBtn.className = 'btn btn-primary disabled';
        processVoiceBtn.disabled = true;
    } else {
        micToggleBtn.className = 'btn btn-primary btn-round';
        micBtnLabel.textContent = 'Iniciar Micrófono';
        
        // Enable processing if there is recorded audio
        processVoiceBtn.className = 'btn btn-secondary';
        processVoiceBtn.disabled = false;
    }
}

function triggerProcessing() {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        alert('El servidor está desconectado.');
        return;
    }

    if (transcribedText && transcribedText.trim() !== "") {
        console.log(`Sending transcribed text directly: ${transcribedText}`);
        socket.send(JSON.stringify({
            type: 'user_transcription',
            text: transcribedText
        }));
    } else {
        console.log("No text transcribed, requesting simulated backend complaint...");
        // Send end_of_speech trigger to get a simulated transcription
        socket.send(JSON.stringify({ type: 'end_of_speech' }));
    }
    
    // Add visual loading bubble
    renderAgentLoading();
    
    // Disable processing button
    processVoiceBtn.className = 'btn btn-secondary disabled';
    processVoiceBtn.disabled = true;
    overlayText.textContent = 'Procesando modelos de Inteligencia Artificial...';
    overlayText.style.color = 'var(--text-secondary)';
}

// ----------------------------------------------------
// Downsampling & Formatting Utilities
// ----------------------------------------------------
function downsampleBuffer(buffer, inputSampleRate, outputSampleRate) {
    if (inputSampleRate === outputSampleRate) {
        return buffer;
    }
    const sampleRateRatio = inputSampleRate / outputSampleRate;
    const newLength = Math.round(buffer.length / sampleRateRatio);
    const result = new Float32Array(newLength);
    
    let offsetResult = 0;
    let offsetBuffer = 0;
    
    while (offsetResult < result.length) {
        const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
        let accum = 0;
        let count = 0;
        for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
            accum += buffer[i];
            count++;
        }
        result[offsetResult] = count > 0 ? accum / count : 0;
        offsetResult++;
        offsetBuffer = nextOffsetBuffer;
    }
    return result;
}

function floatTo16BitPCM(float32Array) {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view = new DataView(buffer);
    let offset = 0;
    
    for (let i = 0; i < float32Array.length; i++, offset += 2) {
        const s = Math.max(-1, Math.min(1, float32Array[i]));
        // Convert to signed 16-bit PCM (little-endian)
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    return buffer;
}

// ----------------------------------------------------
// Animated Canvas Waveform Drawer
// ----------------------------------------------------
function drawWaveform() {
    animationFrameId = requestAnimationFrame(drawWaveform);
    
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Base lines styling
    ctx.lineWidth = 3;
    ctx.shadowBlur = 10;
    
    // If listening and we have analyser data, draw wave from mic
    if (isListening && analyserNode) {
        const bufferLength = analyserNode.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyserNode.getByteTimeDomainData(dataArray);

        ctx.strokeStyle = '#00f2fe';
        ctx.shadowColor = '#00f2fe';
        ctx.beginPath();

        const sliceWidth = width / bufferLength;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
            const v = dataArray[i] / 128.0; // scale
            const y = (v * height) / 2;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
            x += sliceWidth;
        }
        ctx.lineTo(width, height / 2);
        ctx.stroke();
    } else {
        // Draw flat line with subtle periodic wave modulation when processing
        const isProcessing = processVoiceBtn.disabled && !isListening && socket && socket.readyState === WebSocket.OPEN;
        const time = Date.now() * 0.004;
        
        ctx.strokeStyle = isProcessing ? '#c555ec' : '#323d5a';
        ctx.shadowColor = isProcessing ? '#c555ec' : 'transparent';
        ctx.beginPath();
        
        for (let x = 0; x < width; x++) {
            // Processing mode shows small sine ripples
            const amplitude = isProcessing ? 12 * Math.sin(x * 0.02 + time) : 0;
            const y = (height / 2) + amplitude;
            
            if (x === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.stroke();
    }
}

function sendTextInput() {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        alert('El servidor está desconectado.');
        return;
    }

    const text = textQueryInput.value.trim();
    if (!text) return;

    // Clear input
    textQueryInput.value = "";

    console.log(`Sending typed text directly: ${text}`);
    
    // Add visual loading bubble
    renderAgentLoading();
    
    socket.send(JSON.stringify({
        type: 'user_transcription',
        text: text
    }));
}
