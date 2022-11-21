import create from 'zustand'
import { persist } from 'zustand/middleware'

interface SesstionSettings {
    autoupdate: boolean,
    toggleAutoupdate: () => void,
    host: string,
    hostKey: string,
    setHost: (newHost: string, newHostKey: string) => void,
}


export const useSessionSettings = create<SesstionSettings>(
    persist(
        (set) => ({
            autoupdate: false,
            toggleAutoupdate: () => set((state) => ({ autoupdate: !state.autoupdate })),
            host: '',
            hostKey: '',
            setHost: (newHost, newHostKey) => set({ host: newHost, hostKey: newHostKey }),
        }),
        {
            name: 'session-settings'
        }
    )
)
