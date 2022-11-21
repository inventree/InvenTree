import create from 'zustand'
import { persist } from 'zustand/middleware'

interface SesstionSettings {
    autoupdate: boolean,
    toggleAutoupdate: () => void,
}


export const useSessionSettings = create<SesstionSettings>(
    persist(
        (set) => ({
            autoupdate: false,
            toggleAutoupdate: () => set((state) => ({ autoupdate: !state.autoupdate })),
        }),
        {
            name: 'session-settings'
        }
    )
)
