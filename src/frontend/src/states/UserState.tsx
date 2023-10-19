import { create } from 'zustand';

import { api } from '../App';
import { doClassicLogout } from '../functions/auth';
import { ApiPaths, apiUrl } from './ApiState';
import { UserProps } from './states';

interface UserStateProps {
  user: UserProps | undefined;
  username: () => string;
  setUser: (newUser: UserProps) => void;
  fetchUserState: () => void;
}

/**
 * Global user information state, using Zustand manager
 */
export const useUserState = create<UserStateProps>((set, get) => ({
  user: undefined,
  username: () => {
    const user: UserProps = get().user as UserProps;

    if (user?.first_name || user?.last_name) {
      return `${user.first_name} ${user.last_name}`.trim();
    } else {
      return user?.username ?? '';
    }
  },
  setUser: (newUser: UserProps) => set({ user: newUser }),
  fetchUserState: async () => {
    // Fetch user data
    await api
      .get(apiUrl(ApiPaths.user_me), {
        timeout: 5000
      })
      .then((response) => {
        const user: UserProps = {
          first_name: response.data?.first_name ?? '',
          last_name: response.data?.last_name ?? '',
          email: response.data.email,
          username: response.data.username
        };
        set({ user: user });
      })
      .catch((error) => {
        console.error('Error fetching user data:', error);
        // Redirect to login page
        doClassicLogout();
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
