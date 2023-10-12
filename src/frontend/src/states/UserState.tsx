import { create } from 'zustand';

import { api } from '../App';
import { ApiPaths, apiUrl } from './ApiState';
import { UserProps } from './states';

interface UserStateProps {
  user: UserProps | undefined;
  setUser: (newUser: UserProps) => void;
  fetchUserState: () => void;
}

/**
 * Global user information state, using Zustand manager
 */
export const useUserState = create<UserStateProps>((set, get) => ({
  user: undefined,
  setUser: (newUser: UserProps) => set({ user: newUser }),
  fetchUserState: async () => {
    // Fetch user data
    await api
      .get(apiUrl(ApiPaths.user_me))
      .then((response) => {
        const user: UserProps = {
          name: `${response.data.first_name} ${response.data.last_name}`,
          email: response.data.email,
          username: response.data.username
        };
        set({ user: user });
      })
      .catch((error) => {
        console.error('Error fetching user data:', error);
      });

    // Fetch role data
    await api
      .get(apiUrl(ApiPaths.user_roles))
      .then((response) => {
        const user: UserProps = get().user as UserProps;

        // Update user with role data
        user.roles = response.data.roles;
        user.is_staff = response.data.is_staff ?? false;
        user.is_superuser = response.data.is_superuser ?? false;
        set({ user: user });
      })
      .catch((error) => {
        console.error('Error fetching user roles:', error);
      });
  },
  checkUserRole: (role: string, permission: string) => {
    // Check if the user has the specified permission for the specified role
    const user: UserProps = get().user as UserProps;

    if (user.is_superuser) return true;
    if (user.roles === undefined) return false;
    if (user.roles[role] === undefined) return false;

    return user.roles[role].includes(permission);
  }
}));
