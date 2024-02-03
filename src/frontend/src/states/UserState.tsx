import { create } from 'zustand';

import { api } from '../App';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { UserPermissions, UserRoles } from '../enums/Roles';
import { hasToken } from '../functions/auth';
import { apiUrl } from './ApiState';
import { UserProps } from './states';

interface UserStateProps {
  user: UserProps | undefined;
  username: () => string;
  setUser: (newUser: UserProps) => void;
  fetchUserState: () => void;
  checkUserRole: (role: UserRoles, permission: UserPermissions) => boolean;
  hasDeleteRole: (role: UserRoles) => boolean;
  hasChangeRole: (role: UserRoles) => boolean;
  hasAddRole: (role: UserRoles) => boolean;
  hasViewRole: (role: UserRoles) => boolean;
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
    if (!hasToken()) {
      return;
    }

    // Fetch user data
    await api
      .get(apiUrl(ApiEndpoints.user_me), {
        timeout: 2000
      })
      .then((response) => {
        const user: UserProps = {
          pk: response.data.pk,
          first_name: response.data?.first_name ?? '',
          last_name: response.data?.last_name ?? '',
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
      .get(apiUrl(ApiEndpoints.user_roles))
      .then((response) => {
        const user: UserProps = get().user as UserProps;

        // Update user with role data
        user.roles = response.data?.roles ?? {};
        user.is_staff = response.data?.is_staff ?? false;
        user.is_superuser = response.data?.is_superuser ?? false;
        set({ user: user });
      })
      .catch((error) => {
        console.error('Error fetching user roles:', error);
      });
  },
  checkUserRole: (role: UserRoles, permission: UserPermissions) => {
    // Check if the user has the specified permission for the specified role
    const user: UserProps = get().user as UserProps;

    if (!user) {
      return false;
    }

    if (user?.is_superuser) return true;
    if (user?.roles === undefined) return false;
    if (user?.roles[role] === undefined) return false;
    if (user?.roles[role] === null) return false;

    return user?.roles[role]?.includes(permission) ?? false;
  },
  hasDeleteRole: (role: UserRoles) => {
    return get().checkUserRole(role, UserPermissions.delete);
  },
  hasChangeRole: (role: UserRoles) => {
    return get().checkUserRole(role, UserPermissions.change);
  },
  hasAddRole: (role: UserRoles) => {
    return get().checkUserRole(role, UserPermissions.add);
  },
  hasViewRole: (role: UserRoles) => {
    return get().checkUserRole(role, UserPermissions.view);
  }
}));
