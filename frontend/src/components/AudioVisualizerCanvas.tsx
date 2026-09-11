import React, { useEffect, useRef } from 'react';

interface Props {
  isActive: boolean;
  isSpeaking: boolean;
  isListening: boolean;
}

export const AudioVisualizerCanvas: React.FC<Props> = ({ isActive, isSpeaking, isListening }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Initialize Web Audio API Analyser if listening
  useEffect(() => {
    let active = true;

    if (isListening && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then((stream) => {
          if (!active) {
            stream.getTracks().forEach((t) => t.stop());
            return;
          }
          streamRef.current = stream;
          const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
          if (AudioContextClass) {
            const ctx = new AudioContextClass();
            audioContextRef.current = ctx;
            const analyser = ctx.createAnalyser();
            analyser.fftSize = 64;
            analyserRef.current = analyser;

            const source = ctx.createMediaStreamSource(stream);
            source.connect(analyser);
            sourceRef.current = source;
          }
        })
        .catch(() => {
          // Fallback to simulated waveform if mic permission denied
        });
    }

    return () => {
      active = false;
      if (sourceRef.current) {
        sourceRef.current.disconnect();
        sourceRef.current = null;
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      analyserRef.current = null;
    };
  }, [isListening]);

  // Render loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let phase = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const numBars = 32;
      const barWidth = 3;
      const gap = (canvas.width - numBars * barWidth) / (numBars - 1);
      const centerY = canvas.height / 2;

      let freqData: Uint8Array | null = null;
      if (analyserRef.current) {
        freqData = new Uint8Array(analyserRef.current.frequencyBinCount);
        (analyserRef.current as any).getByteFrequencyData(freqData);
      }

      for (let i = 0; i < numBars; i++) {
        let height = 3;

        if (isListening && freqData && freqData.length > 0) {
          const val = freqData[i % freqData.length] / 255;
          height = Math.max(3, val * (canvas.height * 0.85));
        } else if (isSpeaking) {
          // Dynamic harmonic motion when AI speaks
          const wave = Math.sin(phase + i * 0.25) * 0.5 + 0.5;
          const wave2 = Math.cos(phase * 1.5 + i * 0.15) * 0.3 + 0.3;
          height = Math.max(4, (wave + wave2) * (canvas.height * 0.7));
        } else if (isActive) {
          // Ambient breathing idle pulse
          const idleWave = Math.sin(phase * 0.5 + i * 0.2) * 0.5 + 0.5;
          height = 3 + idleWave * 8;
        }

        const x = i * (barWidth + gap);
        const y = centerY - height / 2;

        // Gradient color: Cyan to Emerald when listening, Cyan to Indigo when speaking
        const grad = ctx.createLinearGradient(0, y, 0, y + height);
        if (isSpeaking) {
          grad.addColorStop(0, '#38bdf8'); // sky-400
          grad.addColorStop(1, '#818cf8'); // indigo-400
        } else if (isListening) {
          grad.addColorStop(0, '#34d399'); // emerald-400
          grad.addColorStop(1, '#22d3ee'); // cyan-400
        } else {
          grad.addColorStop(0, '#475569'); // slate-600
          grad.addColorStop(1, '#334155'); // slate-700
        }

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, height, 2);
        ctx.fill();
      }

      phase += 0.08;
      animationFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isActive, isSpeaking, isListening]);

  return (
    <div className="w-full flex items-center justify-center bg-slate-950/70 border border-slate-800/80 rounded-xl px-4 py-3 shadow-inner">
      <canvas ref={canvasRef} width={280} height={40} className="w-full h-10 block" />
    </div>
  );
};
