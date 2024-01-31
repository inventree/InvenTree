import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

import { setApiDefaults } from '../App';
import { useGlobalSettingsState, useUserSettingsState } from './SettingsState';
import { useGlobalStatusState } from './StatusState';
import { useUserState } from './UserState';

interface SessionStateProps {
  token?: string;
  setToken: (newToken?: string) => void;
  loggedIn: boolean;
  setLoggedIn: (isLoggedIn: boolean) => void;
}

/*
 * State manager for user login information.
 */
export const useSessionState = create<SessionStateProps>()(
  persist(
    (set) => ({
      token: '',
      setToken: (newToken) => {
        set({ token: newToken });
        setApiDefaults();
      },
      loggedIn: false,
      setLoggedIn: (isLoggedIn: boolean) => {
        set({ loggedIn: isLoggedIn });
        if (isLoggedIn) {
          // A valid API token has been provided - refetch global state data
          useUserState().fetchUserState();
          useUserSettingsState().fetchSettings();
          useGlobalStatusState().fetchStatus();
          useGlobalSettingsState().fetchSettings();
        }
      }
    }),
    {
      name: 'session-state',
      storage: createJSONStorage(() => sessionStorage)
    }
  )
);
