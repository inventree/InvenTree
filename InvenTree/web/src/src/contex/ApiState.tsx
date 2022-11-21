import create from 'zustand';
import { defaultUser, emptyServerAPI } from '../defaults';
import { UserProps, ServerAPIProps } from './states';


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
}));
