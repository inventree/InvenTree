import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

import { setApiDefaults } from '../App';

interface SessionStateProps {
  token?: string;
  setToken: (newToken?: string) => void;
}

export const useSessionState = create<SessionStateProps>()(
  persist(
    (set) => ({
      token: '',
      setToken: (newToken) => {
        set({ token: newToken });
        setApiDefaults();
      }
    }),
    {
      name: 'session-state',
      storage: createJSONStorage(() => sessionStorage)
    }
  )
);
