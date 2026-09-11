import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X, ShieldCheck } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info' | 'warning' | 'ehr_sync';

export interface ToastItem {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  timestamp: number;
}

interface ToastContextType {
  toasts: ToastItem[];
  showToast: (type: ToastType, title: string, message?: string) => void;
  removeToast: (id: string) => void;
  playChime: (type?: 'connect' | 'disconnect' | 'success' | 'alert') => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const playChime = useCallback((type: 'connect' | 'disconnect' | 'success' | 'alert' = 'success') => {
    try {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioContextClass) return;
      const ctx = new AudioContextClass();

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);

      const now = ctx.currentTime;

      if (type === 'connect') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.15);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
        osc.start(now);
        osc.stop(now + 0.25);
      } else if (type === 'disconnect') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(660, now);
        osc.frequency.exponentialRampToValueAtTime(330, now + 0.18);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
        osc.start(now);
        osc.stop(now + 0.25);
      } else if (type === 'alert') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(880, now);
        osc.frequency.setValueAtTime(440, now + 0.1);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.28);
        osc.start(now);
        osc.stop(now + 0.28);
      } else {
        // Success chime (arpeggiated triad)
        osc.type = 'sine';
        osc.frequency.setValueAtTime(523.25, now); // C5
        osc.frequency.setValueAtTime(659.25, now + 0.08); // E5
        osc.frequency.setValueAtTime(783.99, now + 0.16); // G5
        gain.gain.setValueAtTime(0.06, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
        osc.start(now);
        osc.stop(now + 0.35);
      }
    } catch {
      // Audio context might be restricted before user gesture
    }
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback((type: ToastType, title: string, message?: string) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
    setToasts((prev) => [...prev.slice(-4), { id, type, title, message, timestamp: Date.now() }]);

    if (type === 'success' || type === 'ehr_sync') {
      playChime('success');
    } else if (type === 'error' || type === 'warning') {
      playChime('alert');
    }

    // Auto dismiss after 4.5s
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, [playChime]);

  const getToastIcon = (type: ToastType) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />;
      case 'ehr_sync':
        return <ShieldCheck className="w-4 h-4 text-sky-400 flex-shrink-0" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />;
      default:
        return <Info className="w-4 h-4 text-indigo-400 flex-shrink-0" />;
    }
  };

  const getToastBorder = (type: ToastType) => {
    switch (type) {
      case 'success': return 'border-emerald-500/30 bg-slate-900/95';
      case 'ehr_sync': return 'border-sky-500/30 bg-slate-900/95';
      case 'warning': return 'border-amber-500/30 bg-slate-900/95';
      case 'error': return 'border-rose-500/30 bg-slate-900/95';
      default: return 'border-indigo-500/30 bg-slate-900/95';
    }
  };

  return (
    <ToastContext.Provider value={{ toasts, showToast, removeToast, playChime }}>
      {children}
      {/* Toast Render Stack in Bottom-Right */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col space-y-2.5 max-w-sm w-full pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto border rounded-xl p-3.5 shadow-2xl backdrop-blur-md flex items-start space-x-3 transition-all duration-200 animate-in slide-in-from-right-4 ${getToastBorder(
              toast.type
            )}`}
          >
            {getToastIcon(toast.type)}
            <div className="flex-1 min-w-0">
              <div className="text-xs font-bold text-white tracking-wide">{toast.title}</div>
              {toast.message && (
                <div className="text-[11px] text-slate-400 mt-0.5 leading-relaxed break-words">
                  {toast.message}
                </div>
              )}
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-slate-500 hover:text-white p-0.5 rounded transition"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};
