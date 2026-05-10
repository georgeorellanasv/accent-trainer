class WaveformVisualizer {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.options = {
      barColor: options.barColor || '#CC785C',
      barWidth: options.barWidth || 3,
      barGap: options.barGap || 1,
      backgroundColor: options.backgroundColor || '#FFFFFF',
      ...options
    };
    this.audioData = null;
  }

  async loadAudio(audioBlob) {
    const arrayBuffer = await audioBlob.arrayBuffer();
    const audioContext = new AudioContext();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    this.audioData = audioBuffer.getChannelData(0);
    await audioContext.close();
    this.draw();
  }

  async loadFromUrl(url) {
    const response = await fetch(url);
    const blob = await response.blob();
    await this.loadAudio(blob);
  }

  draw() {
    if (!this.audioData) return;

    const { width, height } = this.canvas;
    const { barColor, barWidth, barGap, backgroundColor } = this.options;

    // Clear canvas
    this.ctx.fillStyle = backgroundColor;
    this.ctx.fillRect(0, 0, width, height);

    // Calculate bars
    const totalBars = Math.floor(width / (barWidth + barGap));
    const samplesPerBar = Math.floor(this.audioData.length / totalBars);

    this.ctx.fillStyle = barColor;

    for (let i = 0; i < totalBars; i++) {
      // Get average amplitude for this bar
      let sum = 0;
      const start = i * samplesPerBar;
      for (let j = 0; j < samplesPerBar; j++) {
        sum += Math.abs(this.audioData[start + j] || 0);
      }
      const avg = sum / samplesPerBar;

      // Scale to canvas height
      const barHeight = Math.max(2, avg * height * 2);
      const x = i * (barWidth + barGap);
      const y = (height - barHeight) / 2;

      // Draw rounded bar
      this.ctx.beginPath();
      this.ctx.roundRect(x, y, barWidth, barHeight, barWidth / 2);
      this.ctx.fill();
    }
  }

  clear() {
    const { width, height } = this.canvas;
    this.ctx.fillStyle = this.options.backgroundColor;
    this.ctx.fillRect(0, 0, width, height);
    this.audioData = null;
  }
}

// Audio recorder with waveform
class AudioRecorder {
  constructor(options = {}) {
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.stream = null;
    this.onDataAvailable = options.onDataAvailable || (() => {});
    this.onStop = options.onStop || (() => {});
  }

  async start() {
    this.audioChunks = [];
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm';

    this.mediaRecorder = new MediaRecorder(this.stream, { mimeType });

    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        this.audioChunks.push(e.data);
        this.onDataAvailable(e.data);
      }
    };

    this.mediaRecorder.onstop = () => {
      const blob = new Blob(this.audioChunks, { type: 'audio/webm' });
      this.onStop(blob);
    };

    this.mediaRecorder.start(100);
  }

  stop() {
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop();
    }
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
    }
  }

  isRecording() {
    return this.mediaRecorder && this.mediaRecorder.state === 'recording';
  }
}

// Convert webm to wav for Azure
async function convertToWav(webmBlob) {
  const arrayBuffer = await webmBlob.arrayBuffer();
  const audioCtx = new AudioContext();
  const decoded = await audioCtx.decodeAudioData(arrayBuffer);
  await audioCtx.close();

  // Resample to 16kHz mono
  const targetRate = 16000;
  const offCtx = new OfflineAudioContext(
    1,
    Math.ceil(decoded.duration * targetRate),
    targetRate
  );
  const src = offCtx.createBufferSource();
  src.buffer = decoded;
  src.connect(offCtx.destination);
  src.start();
  const resampled = await offCtx.startRendering();

  const samples = resampled.getChannelData(0);
  const pcm = new Int16Array(samples.length);
  for (let i = 0; i < samples.length; i++) {
    pcm[i] = Math.max(-32768, Math.min(32767, samples[i] * 32768));
  }

  // Create WAV
  const wavBuf = new ArrayBuffer(44 + pcm.buffer.byteLength);
  const v = new DataView(wavBuf);
  const writeStr = (off, s) => [...s].forEach((c, i) => v.setUint8(off + i, c.charCodeAt(0)));

  writeStr(0, 'RIFF');
  v.setUint32(4, 36 + pcm.buffer.byteLength, true);
  writeStr(8, 'WAVE');
  writeStr(12, 'fmt ');
  v.setUint32(16, 16, true);
  v.setUint16(20, 1, true);
  v.setUint16(22, 1, true);
  v.setUint32(24, targetRate, true);
  v.setUint32(28, targetRate * 2, true);
  v.setUint16(32, 2, true);
  v.setUint16(34, 16, true);
  writeStr(36, 'data');
  v.setUint32(40, pcm.buffer.byteLength, true);
  new Int16Array(wavBuf, 44).set(pcm);

  return new Blob([wavBuf], { type: 'audio/wav' });
}

// Export for use
window.WaveformVisualizer = WaveformVisualizer;
window.AudioRecorder = AudioRecorder;
window.convertToWav = convertToWav;
