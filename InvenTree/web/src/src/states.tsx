import create from 'zustand'
import { persist } from 'zustand/middleware'

// helpers
export interface HostProps {
    host: string,
    name: string,
}

export interface HostList {
    [key: string]: HostProps
}

// states
interface SesstionSettings {
    autoupdate: boolean,
    toggleAutoupdate: () => void,
    host: string,
    hostKey: string,
    hostList: HostList,
    setHost: (newHost: string, newHostKey: string) => void,
}


export const useSessionSettings = create<SesstionSettings>(
    persist(
        (set) => ({
            autoupdate: false,
            toggleAutoupdate: () => set((state) => ({ autoupdate: !state.autoupdate })),
            host: '',
            hostKey: '',
            hostList: {},
            setHost: (newHost, newHostKey) => set({ host: newHost, hostKey: newHostKey }),
        }),
        {
            name: 'session-settings'
        }
    )
)
