import { QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
import { RouterProvider } from 'react-router-dom';

import { queryClient, setApiDefaults } from './App';
import { useApiState } from './context/ApiState';
import { BaseContext } from './context/BaseContext';
import { useLocalState } from './context/LocalState';
import { useSessionState } from './context/SessionState';
import { defaultHostList } from './defaults';
import { router } from './router';

export default function DesktopAppView() {
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

  return (
    <BaseContext>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </BaseContext>
  );
}
