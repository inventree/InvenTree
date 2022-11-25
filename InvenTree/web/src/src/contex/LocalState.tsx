import create from 'zustand';
import { persist } from 'zustand/middleware';
import { HostList } from './states';

interface LocalStateProps {
  autoupdate: boolean;
  toggleAutoupdate: () => void;
  host: string;
  setHost: (newHost: string, newHostKey: string) => void;
  hostKey: string;
  hostList: HostList;
  lastUsername: string;
  primaryColor: string;
}

export const useLocalState = create<LocalStateProps>()(
  persist(
    (set) => ({
      autoupdate: false,
      toggleAutoupdate: () =>
        set((state) => ({ autoupdate: !state.autoupdate })),
      host: '',
      setHost: (newHost, newHostKey) =>
        set({ host: newHost, hostKey: newHostKey }),
      lastUsername: '',
      hostKey: '',
      hostList: {},
      primaryColor: 'green',
    }),
    {
      name: 'session-settings'
    }
  )
);
