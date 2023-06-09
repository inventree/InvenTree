import create from 'zustand';
import { api } from '../App';
import { defaultUser, emptyServerAPI } from '../defaults';
import { UserProps, ServerAPIProps } from './states';

interface ApiStateProps {
  user: UserProps;
  setUser: (newUser: UserProps) => void;
  server: ServerAPIProps;
  setServer: (newServer: ServerAPIProps) => void;
  fetchApiState: () => void;
}

export const useApiState = create<ApiStateProps>((set) => ({
  user: defaultUser,
  setUser: (newUser: UserProps) => set({ user: newUser }),
  server: emptyServerAPI,
  setServer: (newServer: ServerAPIProps) => set({ server: newServer }),
  fetchApiState: async () => {
    // Fetch user data
    await api.get('/user/me/').then((response) => {
      const user: UserProps = {
        name: `${response.data.first_name} ${response.data.last_name}`,
        email: response.data.email,
        username: response.data.username
      };
      set({ user: user });
    });
    // Fetch server data
    await api.get('/').then((response) => {
      set({ server: response.data });
    });
  },
}));
