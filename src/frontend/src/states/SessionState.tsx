import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import { setApiDefaults } from '../App';

interface SessionStateProps {
  token: string | undefined;
  setToken: (newToken: string | undefined) => void;
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
      getStorage: () => sessionStorage
    }
  )
);
