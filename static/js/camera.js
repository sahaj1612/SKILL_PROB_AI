// Camera, microphone, and privacy-preserving interview integrity signals.
// Video stays in the browser. Only aggregate event counts are sent at the end.
class CameraManager {
    constructor() {
        this.cameraStream = null; this.audioStream = null; this.isCameraOn = false; this.isMicOn = false;
        this.videoElement = document.getElementById('camera-feed'); this.cameraOffElement = document.getElementById('camera-off');
        this.toggleCameraBtn = document.getElementById('toggle-camera'); this.toggleMicBtn = document.getElementById('toggle-mic');
        this.monitor = new InterviewIntegrityMonitor(this.videoElement); this.init();
    }
    init() {
        this.toggleCameraBtn?.addEventListener('click', () => this.isCameraOn ? this.stopCamera() : this.startCamera());
        this.toggleMicBtn?.addEventListener('click', () => this.isMicOn ? this.stopMicrophone() : this.startMicrophone()); this.showCameraOff();
    }
    async startCamera() {
        try {
            this.cameraStream = await navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }, audio: false });
            this.videoElement.srcObject = this.cameraStream; this.isCameraOn = true; this.showCameraOn(); this.updateCameraButton(true); await this.monitor.start();
        } catch (error) { console.error('Error accessing camera:', error); alert(error.name === 'NotAllowedError' ? 'Camera access is blocked. Please allow it in browser settings.' : 'Could not access the camera. Please check that it is available.'); }
    }
    async stopCamera() { this.monitor.stop(); this.cameraStream?.getTracks().forEach(track => track.stop()); this.cameraStream = null; this.videoElement.srcObject = null; this.isCameraOn = false; this.showCameraOff(); this.updateCameraButton(false); }
    async startMicrophone() {
        try { this.audioStream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }, video: false }); this.isMicOn = true; this.updateMicrophoneButton(true); }
        catch (error) { console.error('Error accessing microphone:', error); alert('Could not access the microphone. Please check browser permissions.'); }
    }
    async stopMicrophone() { this.audioStream?.getTracks().forEach(track => track.stop()); this.audioStream = null; this.isMicOn = false; this.updateMicrophoneButton(false); }
    updateCameraButton(isOn) {
        if (!this.toggleCameraBtn) return; this.toggleCameraBtn.innerHTML = isOn ? '<i class="fas fa-video-slash mr-1"></i> Turn Off Camera' : '<i class="fas fa-video mr-1"></i> Turn On Camera';
        this.toggleCameraBtn.classList.toggle('bg-red-600', isOn); this.toggleCameraBtn.classList.toggle('hover:bg-red-700', isOn); this.toggleCameraBtn.classList.toggle('bg-blue-600', !isOn); this.toggleCameraBtn.classList.toggle('hover:bg-blue-700', !isOn);
    }
    updateMicrophoneButton(isOn) {
        if (!this.toggleMicBtn) return; this.toggleMicBtn.innerHTML = isOn ? '<i class="fas fa-microphone-slash mr-1"></i> Mute' : '<i class="fas fa-microphone mr-1"></i> Unmute';
        this.toggleMicBtn.classList.toggle('bg-red-600', isOn); this.toggleMicBtn.classList.toggle('hover:bg-red-700', isOn); this.toggleMicBtn.classList.toggle('bg-green-600', !isOn); this.toggleMicBtn.classList.toggle('hover:bg-green-700', !isOn);
    }
    showCameraOn() { this.videoElement?.classList.remove('hidden'); this.cameraOffElement?.classList.add('hidden'); }
    showCameraOff() { this.videoElement?.classList.add('hidden'); this.cameraOffElement?.classList.remove('hidden'); }
    stopAll() { this.stopCamera(); this.stopMicrophone(); }
}

class InterviewIntegrityMonitor {
    constructor(videoElement) {
        this.video = videoElement; this.landmarker = null; this.timer = null; this.startedAt = null;
        this.metrics = { samples: 0, facePresent: 0, eyesVisible: 0, cameraFacing: 0, noFaceEvents: 0, multipleFaceEvents: 0, lookingAwayEvents: 0, obstructionEvents: 0, poorLightingEvents: 0 };
    }
    async start() {
        this.startedAt ||= Date.now(); this.setStatus('Starting local camera check…', 'text-yellow-600');
        try {
            const vision = await import('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14');
            const fileset = await vision.FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm');
            this.landmarker = await vision.FaceLandmarker.createFromOptions(fileset, { baseOptions: { modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task' }, runningMode: 'VIDEO', numFaces: 2, outputFaceBlendshapes: false });
            this.timer = window.setInterval(() => this.sample(), 900); this.setStatus('Monitoring locally: waiting for face', 'text-yellow-600');
        } catch (error) { console.warn('Local face analysis unavailable:', error); this.setStatus('Camera on — local face analysis unavailable', 'text-gray-500'); }
    }
    stop() { if (this.timer) window.clearInterval(this.timer); this.timer = null; this.landmarker?.close?.(); this.landmarker = null; }
    sample() {
        if (!this.landmarker || this.video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) return;
        const result = this.landmarker.detectForVideo(this.video, performance.now()); const faces = result.faceLandmarks || []; this.metrics.samples++;
        const brightness = this.frameBrightness(); let state = 'Face detected', statusClass = 'text-green-600';
        if (brightness !== null && brightness < 30) { this.metrics.poorLightingEvents++; state = 'Low light / possible lens obstruction'; statusClass = 'text-yellow-600'; }
        if (!faces.length) { this.metrics.noFaceEvents++; state = 'No face detected'; statusClass = 'text-yellow-600'; }
        else {
            this.metrics.facePresent++; if (faces.length > 1) { this.metrics.multipleFaceEvents++; state = 'More than one face detected'; statusClass = 'text-red-600'; }
            const face = faces[0]; if (this.eyesVisible(face)) this.metrics.eyesVisible++; else { this.metrics.obstructionEvents++; state = 'Eyes not clearly visible'; statusClass = 'text-yellow-600'; }
            if (this.lookingAtScreen(face)) this.metrics.cameraFacing++; else if (faces.length === 1) { this.metrics.lookingAwayEvents++; state = 'Looking away from screen'; statusClass = 'text-yellow-600'; }
        }
        this.setStatus(state, statusClass);
    }
    eyesVisible(points) { return points.length >= 478 && points[33] && points[263] && points[468] && points[473]; }
    lookingAtScreen(points) {
        if (!this.eyesVisible(points)) return false; const within = (iris, a, b) => { const min = Math.min(a.x, b.x), max = Math.max(a.x, b.x); const x = (iris.x - min) / Math.max(max - min, 0.001); return x > 0.18 && x < 0.82; };
        return within(points[468], points[33], points[133]) && within(points[473], points[362], points[263]);
    }
    frameBrightness() {
        const canvas = this.canvas ||= document.createElement('canvas'); canvas.width = 32; canvas.height = 24; const ctx = canvas.getContext('2d', { willReadFrequently: true });
        try { ctx.drawImage(this.video, 0, 0, canvas.width, canvas.height); const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data; let total = 0; for (let i = 0; i < data.length; i += 4) total += (data[i] + data[i + 1] + data[i + 2]) / 3; return total / (data.length / 4); } catch (_) { return null; }
    }
    setStatus(text, colorClass) { const el = document.getElementById('integrity-status'); if (el) { el.textContent = text; el.className = `text-sm font-medium ${colorClass}`; } }
    summary() {
        const m = this.metrics, samples = Math.max(m.samples, 1); return { monitored_seconds: this.startedAt ? Math.round((Date.now() - this.startedAt) / 1000) : 0, samples: m.samples, face_visible_percent: Math.round(m.facePresent / samples * 100), eyes_visible_percent: Math.round(m.eyesVisible / samples * 100), screen_facing_percent: Math.round(m.cameraFacing / samples * 100), no_face_events: m.noFaceEvents, multiple_face_events: m.multipleFaceEvents, looking_away_events: m.lookingAwayEvents, obstruction_events: m.obstructionEvents, poor_lighting_events: m.poorLightingEvents, analysis_available: Boolean(this.startedAt && m.samples) };
    }
    snapshot() { return { capturedAt: Date.now(), ...this.metrics }; }
    summarySince(snapshot) {
        const start = snapshot || {}, m = this.metrics;
        const value = key => Math.max(0, (m[key] || 0) - (start[key] || 0));
        const samples = value('samples'), divisor = Math.max(samples, 1);
        return { monitored_seconds: start.capturedAt ? Math.max(0, Math.round((Date.now() - start.capturedAt) / 1000)) : 0, samples, face_visible_percent: Math.round(value('facePresent') / divisor * 100), eyes_visible_percent: Math.round(value('eyesVisible') / divisor * 100), screen_facing_percent: Math.round(value('cameraFacing') / divisor * 100), no_face_events: value('noFaceEvents'), multiple_face_events: value('multipleFaceEvents'), looking_away_events: value('lookingAwayEvents'), obstruction_events: value('obstructionEvents'), poor_lighting_events: value('poorLightingEvents'), analysis_available: Boolean(this.startedAt && samples) };
    }
    async saveSummary() { try { await fetch('/api/integrity-summary', { method: 'POST', headers: { 'Content-Type': 'application/json' }, keepalive: true, body: JSON.stringify(this.summary()) }); } catch (error) { console.warn('Could not save integrity summary:', error); } }
}
document.addEventListener('DOMContentLoaded', () => { window.cameraManager = new CameraManager(); });
