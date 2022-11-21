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

interface UserStateProps {
    name: string,
    email: string,
    username: string,
    setUser: (newUser: UserProps) => void,
}

export const useUserState = create<UserStateProps>((set) => ({
    name: user.name,
    email: user.email,
    username: user.username,
    setUser: (newUser: UserProps) => set({ name: newUser.name, email: newUser.email, username: newUser.username }),
}))
