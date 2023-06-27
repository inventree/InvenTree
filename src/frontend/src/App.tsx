import * as Sentry from '@sentry/react';
import { BrowserTracing } from '@sentry/tracing';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import axios from 'axios';
import { useState } from 'react';
import { RouterProvider } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { useLocalState } from './context/LocalState';
import { useSessionState } from './context/SessionState';
import { defaultHostList } from './defaults';
import { ThemeContext } from './context/ThemeContext';
import { LanguageContext } from './context/LanguageContext';
import { useApiState } from './context/ApiState';
import { router } from './router';

const LOAD_SENTRY = false;

// Error tracking
if (LOAD_SENTRY) {
  Sentry.init({
    dsn: 'https://84f0c3ea90c64e5092e2bf5dfe325725@o1047628.ingest.sentry.io/4504160008273920',
    integrations: [new BrowserTracing()],
    tracesSampleRate: 1.0
  });
}

// API
export const api = axios.create({});
export function setApiDefaults() {
  const host = useLocalState.getState().host;
  const token = useSessionState.getState().token;

  api.defaults.baseURL = host;
  api.defaults.headers.common['Authorization'] = `Token ${token}`;
}
export const queryClient = new QueryClient();

// Main App
export default function App() {
  const [hostList] = useLocalState((state) => [state.hostList]);
  const [fetchApiState] = useApiState((state) => [state.fetchApiState]);

  // Local state initialization
  if (Object.keys(hostList).length === 0) {
    console.log('Loading default host list');
    useLocalState.setState({ hostList: defaultHostList });
  }
  setApiDefaults();

  // Server Session
  const [fetchedServerSession, setFetchedServerSession] = useState(false);
  const sessionState = useSessionState.getState();
  const [token] = sessionState.token ? [sessionState.token] : [null];
  if (token && !fetchedServerSession) {
    setFetchedServerSession(true);
    fetchApiState();
  }

  // Main App component
  return (
    <LanguageContext>
      <ThemeContext>
        <AuthProvider>
          <QueryClientProvider client={queryClient}>
            <RouterProvider router={router} />
          </QueryClientProvider>
        </AuthProvider>
      </ThemeContext>
    </LanguageContext>
  );
}
