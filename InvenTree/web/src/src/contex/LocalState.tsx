import create from 'zustand';
import { persist } from 'zustand/middleware';
import { HostList } from './states';

interface LocalStateProps {
    autoupdate: boolean;
    toggleAutoupdate: () => void;
    host: string;
    hostKey: string;
    hostList: HostList;
    setHost: (newHost: string, newHostKey: string) => void;
    lastUsername: string;
}

export const useLocalState = create<LocalStateProps>()(
    persist(
        (set) => ({
            autoupdate: false,
            toggleAutoupdate: () => set((state) => ({ autoupdate: !state.autoupdate })),
            host: '',
            hostKey: '',
            hostList: {},
            setHost: (newHost, newHostKey) => set({ host: newHost, hostKey: newHostKey }),
            lastUsername: '',
        }),
        {
            name: 'session-settings'
        }
    )
);
