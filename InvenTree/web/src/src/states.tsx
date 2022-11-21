import create from 'zustand'
import { persist } from 'zustand/middleware'
import { setApiDefaults } from './App'
import { defaultUser } from './defaults'

// helpers
export interface HostList {
    [key: string]: {
        host: string,
        name: string,
    }
}

export interface UserProps {
    name: string,
    email: string,
    username: string
}

export interface ServerAPIProps {
    server: null | string;
    version: null | string;
    instance: null | string;
    apiVersion: null | number;
    worker_running: null | boolean;
    worker_pending_tasks: null | number;
    plugins_enabled: null | boolean;
    active_plugins: PluginProps[];
}

export interface PluginProps {
    name: string;
    slug: string;
    version: null | string;
}

const emptyServerAPI: ServerAPIProps = {
    server: null,
    version: null,
    instance: null,
    apiVersion: null,
    worker_running: null,
    worker_pending_tasks: null,
    plugins_enabled: null,
    active_plugins: [],
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


export const useSessionSettings = create<SesstionSettings>()(
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
    server: ServerAPIProps,
    setServer: (newServer: ServerAPIProps) => void,
}

export const useApiState = create<ApiStateProps>((set) => ({
    user: defaultUser,
    setUser: (newUser: UserProps) => set({ user: newUser }),
    server: emptyServerAPI,
    setServer: (newServer: ServerAPIProps) => set({ server: newServer }),
}))

interface SessionStateProps {
    token: string,
    setToken: (newToken: string) => void,
}

export const useSessionState = create<SessionStateProps>()(
    persist(
        (set) => ({
            token: '',
            setToken: (newToken) => {
                set({ token: newToken });
                setApiDefaults();
            },
        }),
        {
            name: 'session-state',
            getStorage: () => sessionStorage,
        }
    )
)
