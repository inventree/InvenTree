import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

import { setApiDefaults } from '../App';
import { useGlobalSettingsState, useUserSettingsState } from './SettingsState';
import { useGlobalStatusState } from './StatusState';
import { useUserState } from './UserState';
import { fetchGlobalStates } from './states';

interface SessionStateProps {
  token?: string;
  setToken: (newToken?: string) => void;
  clearToken: () => void;
  hasToken: () => boolean;
}

/*
 * State manager for user login information.
 */
export const useSessionState = create<SessionStateProps>()(
  persist(
    (set, get) => ({
      token: undefined,
      clearToken: () => {
        set({ token: undefined });
      },
      setToken: (newToken) => {
        set({ token: newToken });

        setApiDefaults();
        fetchGlobalStates();
      },
      hasToken: () => !!get().token
    }),
    {
      name: 'session-state',
      storage: createJSONStorage(() => sessionStorage)
    }
  )
);
