import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './hooks/useAuth';
import { ToastProvider } from './context/ToastContext';
import { PlatformEventProvider } from './context/PlatformEventContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import { App } from './App';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <PlatformEventProvider>
            <AuthProvider>
              <App />
            </AuthProvider>
          </PlatformEventProvider>
        </ToastProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>
);
