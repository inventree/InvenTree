import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import axios from 'axios';
import { useState } from 'react';
import { RouterProvider } from 'react-router-dom';

import { useApiState } from './context/ApiState';
import { LanguageContext } from './context/LanguageContext';
import { useLocalState } from './context/LocalState';
import { useSessionState } from './context/SessionState';
import { ThemeContext } from './context/ThemeContext';
import { defaultHostList } from './defaults';
import { router } from './router';

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
        <QueryClientProvider client={queryClient}>
          <RouterProvider router={router} />
        </QueryClientProvider>
      </ThemeContext>
    </LanguageContext>
  );
}
