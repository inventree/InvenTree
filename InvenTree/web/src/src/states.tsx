import create from 'zustand'
import { persist } from 'zustand/middleware'

// helpers
export interface HostList {
    [key: string]:  {
        host: string,
        name: string,
    }
}

export interface UserProps {
    name: string,
    email: string,
    username: string
}

const user = {
    name: "Matthias Mair",
    email: "code@mjmair.com",
    username: "mjmair",
};

// States
interface SesstionSettings {
    autoupdate: boolean,
    toggleAutoupdate: () => void,
    host: string,
    hostKey: string,
    hostList: HostList,
    setHost: (newHost: string, newHostKey: string) => void,
    lastUsername: string,
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
            lastUsername: '',
        }),
        {
            name: 'session-settings'
        }
    )
)

interface ApiStateProps {
    user: UserProps,
    setUser: (newUser: UserProps) => void,
}

export const useApiState = create<ApiStateProps>((set) => ({
    user: user,
    setUser: (newUser: UserProps) => set({ user: newUser }),
}))

interface SessionStateProps {
    token: string,
    setToken: (newToken: string) => void,
}

export const useSessionState = create<SessionStateProps>()(
    persist(
        (set) => ({
            token: '',
            setToken: (newToken) => set({ token: newToken }),
        }),
        {
            name: 'session-state',
            getStorage: () => sessionStorage,
        }
    )
)
