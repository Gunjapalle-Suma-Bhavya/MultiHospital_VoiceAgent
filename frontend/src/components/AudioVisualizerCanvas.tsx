import React, { useEffect, useRef } from 'react';

interface Props {
  isActive: boolean;
  isSpeaking: boolean;
  isListening: boolean;
}

export const AudioVisualizerCanvas: React.FC<Props> = ({ isActive, isSpeaking, isListening }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Render loop using harmonic waveform generator (no microphone locking collisions)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let phase = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const numBars = 36;
      const barWidth = 3;
      const centerY = canvas.height / 2;

      for (let i = 0; i < numBars; i++) {
        let height = 3;

        if (isListening) {
          // Dynamic pulsing audio frequencies when patient is speaking into mic
          const w1 = Math.sin(phase * 1.8 + i * 0.3) * 0.5 + 0.5;
          const w2 = Math.cos(phase * 2.4 + i * 0.2) * 0.4 + 0.4;
          const jitter = Math.sin(i * 1.7) * 0.2;
          height = Math.max(4, (w1 + w2 + jitter) * (canvas.height * 0.8));
        } else if (isSpeaking) {
          // Natural speech synthesis cadence when AI is speaking back
          const wave = Math.sin(phase * 1.2 + i * 0.25) * 0.5 + 0.5;
          const wave2 = Math.cos(phase * 1.5 + i * 0.15) * 0.3 + 0.3;
          height = Math.max(4, (wave + wave2) * (canvas.height * 0.7));
        } else if (isActive) {
          // Ambient breathing state
          const wave = Math.sin(phase * 0.6 + i * 0.2) * 0.25 + 0.25;
          height = Math.max(3, wave * (canvas.height * 0.35));
        }

        // Color palette based on status
        let gradient = ctx.createLinearGradient(0, centerY - height / 2, 0, centerY + height / 2);
        if (isListening) {
          gradient.addColorStop(0, '#f43f5e'); // Rose / red when recording
          gradient.addColorStop(0.5, '#fb7185');
          gradient.addColorStop(1, '#f43f5e');
        } else if (isSpeaking) {
          gradient.addColorStop(0, '#38bdf8'); // Sky blue when AI speaking
          gradient.addColorStop(0.5, '#0ea5e9');
          gradient.addColorStop(1, '#38bdf8');
        } else {
          gradient.addColorStop(0, '#10b981'); // Emerald when idle / ready
          gradient.addColorStop(0.5, '#059669');
          gradient.addColorStop(1, '#10b981');
        }

        ctx.fillStyle = gradient;
        const x = (canvas.width / numBars) * i + (canvas.width / numBars - barWidth) / 2;
        const y = centerY - height / 2;
        const radius = barWidth / 2;

        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, height, radius);
        ctx.fill();
      }

      phase += isListening ? 0.08 : isSpeaking ? 0.06 : 0.02;
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
    <div className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 flex flex-col items-center justify-center space-y-1">
      <div className="flex justify-between items-center w-full px-2 text-[10px] font-mono text-slate-500">
        <span className="flex items-center space-x-1">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              isListening ? 'bg-rose-500 animate-ping' : isSpeaking ? 'bg-sky-400 animate-pulse' : 'bg-emerald-500'
            }`}
          />
          <span className="uppercase">
            {isListening ? 'Active Microphone (Speech In)' : isSpeaking ? 'Synthesizer (Audio Out)' : 'Web Audio Pipeline Ready'}
          </span>
        </span>
        <span>Sub-180ms Barge-In</span>
      </div>

      <canvas
        ref={canvasRef}
        width={360}
        height={48}
        className="w-full max-w-md h-12 rounded-lg"
      />
    </div>
  );
};
