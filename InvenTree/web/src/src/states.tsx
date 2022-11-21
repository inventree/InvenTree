import create from 'zustand'
import { persist } from 'zustand/middleware'

interface SesstionSettings {
    autoupdate: boolean,
    setAutoupdate: (autoupdate: boolean) => void,
    toffleAutoupdate: () => void,
}


export const useSessionSettings = create<SesstionSettings>(
    persist((set) => ({
        autoupdate: false,
        setAutoupdate: (value) => set({ autoupdate: value }),
        toffleAutoupdate: () => set((state) => ({ autoupdate: !state.autoupdate })),
    }),
        {
            name: 'session-settings'
        }
    )
)
