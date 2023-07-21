import { QueryClientProvider } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { RouterProvider } from 'react-router-dom';

import { queryClient, setApiDefaults } from '../App';
import { BaseContext } from '../contexts/BaseContext';
import { defaultHostList } from '../defaults/defaultHostList';
import { router } from '../router';
import { useApiState } from '../states/ApiState';
import { useLocalState } from '../states/LocalState';
import { useSessionState } from '../states/SessionState';

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
  useEffect(() => {
    if (token && !fetchedServerSession) {
      setFetchedServerSession(true);
      fetchApiState();
    }
  }, [token, fetchedServerSession]);

  return (
    <BaseContext>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </BaseContext>
  );
}
