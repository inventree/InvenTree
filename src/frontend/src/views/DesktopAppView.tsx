import { QueryClientProvider } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { BrowserRouter } from 'react-router-dom';

import { queryClient } from '../App';
import { BaseContext } from '../contexts/BaseContext';
import { defaultHostList } from '../defaults/defaultHostList';
import { hasToken } from '../functions/auth';
import { base_url } from '../main';
import { routes } from '../router';
import { useLocalState } from '../states/LocalState';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../states/SettingsState';
import { useUserState } from '../states/UserState';

export default function DesktopAppView() {
  const [hostList] = useLocalState((state) => [state.hostList]);
  const [fetchUserState] = useUserState((state) => [state.fetchUserState]);

  const [fetchGlobalSettings] = useGlobalSettingsState((state) => [
    state.fetchSettings
  ]);
  const [fetchUserSettings] = useUserSettingsState((state) => [
    state.fetchSettings
  ]);

  // Server Session
  const [fetchedServerSession, setFetchedServerSession] = useState(false);
  useEffect(() => {
    if (Object.keys(hostList).length === 0) {
      useLocalState.setState({ hostList: defaultHostList });
    }

    if (hasToken(true) && !fetchedServerSession) {
      setFetchedServerSession(true);
      fetchUserState();
      fetchGlobalSettings();
      fetchUserSettings();
    }
  }, [fetchedServerSession]);

  return (
    <BaseContext>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter basename={base_url}>{routes}</BrowserRouter>
      </QueryClientProvider>
    </BaseContext>
  );
}
