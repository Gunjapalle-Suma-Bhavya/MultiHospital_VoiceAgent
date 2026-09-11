import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertOctagon, RotateCcw, HeartPulse } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error caught by ErrorBoundary:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
          <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 text-center space-y-4 shadow-2xl">
            <div className="w-12 h-12 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 mx-auto flex items-center justify-center">
              <AlertOctagon className="w-6 h-6" />
            </div>

            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-rose-400">Clinical Safety Shield</div>
              <h2 className="text-xl font-black text-white mt-1">Application State Recovered</h2>
              <p className="text-xs text-slate-400 mt-1">
                A localized client interface exception occurred. Your medical sessions and backend EHR records remain secure.
              </p>
            </div>

            {this.state.error && (
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-left font-mono text-[11px] text-rose-300 max-h-32 overflow-y-auto">
                {this.state.error.message}
              </div>
            )}

            <button
              onClick={() => window.location.reload()}
              className="w-full inline-flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition shadow-lg shadow-emerald-500/20"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Reload Medical Workspace</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
