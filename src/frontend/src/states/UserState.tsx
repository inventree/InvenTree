import { create } from 'zustand';

import { api, setApiDefaults } from '../App';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import type { ModelType } from '../enums/ModelType';
import { UserPermissions, type UserRoles } from '../enums/Roles';
import { clearCsrfCookie } from '../functions/auth';
import { apiUrl } from './ApiState';
import type { UserProps } from './states';

export interface UserStateProps {
  user: UserProps | undefined;
  is_authed: boolean;
  userId: () => number | undefined;
  username: () => string;
  setUser: (newUser: UserProps) => void;
  setAuthenticated: (authed?: boolean) => void;
  fetchUserToken: () => Promise<void>;
  fetchUserState: () => Promise<void>;
  clearUserState: () => void;
  checkUserRole: (role: UserRoles, permission: UserPermissions) => boolean;
  hasDeleteRole: (role: UserRoles) => boolean;
  hasChangeRole: (role: UserRoles) => boolean;
  hasAddRole: (role: UserRoles) => boolean;
  hasViewRole: (role: UserRoles) => boolean;
  checkUserPermission: (
    model: ModelType,
    permission: UserPermissions
  ) => boolean;
  hasDeletePermission: (model: ModelType) => boolean;
  hasChangePermission: (model: ModelType) => boolean;
  hasAddPermission: (model: ModelType) => boolean;
  hasViewPermission: (model: ModelType) => boolean;
  isAuthed: () => boolean;
  isLoggedIn: () => boolean;
  isStaff: () => boolean;
  isSuperuser: () => boolean;
}

/**
 * Global user information state, using Zustand manager
 */
export const useUserState = create<UserStateProps>((set, get) => ({
  user: undefined,
  is_authed: false,
  setAuthenticated: (authed = true) => {
    set({ is_authed: authed });
    setApiDefaults();
  },
  userId: () => {
    const user: UserProps = get().user as UserProps;
    return user.pk;
  },
  username: () => {
    const user: UserProps = get().user as UserProps;

    if (user?.first_name || user?.last_name) {
      return `${user.first_name} ${user.last_name}`.trim();
    } else {
      return user?.username ?? '';
    }
  },
  setUser: (newUser: UserProps) => set({ user: newUser }),
  clearUserState: () => {
    set({ user: undefined, is_authed: false });
    clearCsrfCookie();
    setApiDefaults();
  },
  fetchUserToken: async () => {
    // If neither the csrf or session cookies are available, we cannot fetch a token
    if (
      !document.cookie.includes('csrftoken') &&
      !document.cookie.includes('sessionid')
    ) {
      get().setAuthenticated(false);
      return;
    }

    await api
      .get(apiUrl(ApiEndpoints.user_token))
      .then((response) => {
        if (response.status == 200 && response.data.token) {
          get().setAuthenticated(response.data.token);
        } else {
          get().setAuthenticated(false);
        }
      })
      .catch(() => {
        get().setAuthenticated(false);
      });
  },
  fetchUserState: async () => {
    if (!get().isAuthed()) {
      await get().fetchUserToken();
    }

    // If we still don't have a token, clear the user state and return
    if (!get().isAuthed()) {
      get().clearUserState();
      return;
    }

    // Fetch user data
    await api
      .get(apiUrl(ApiEndpoints.user_me), {
        timeout: 2000
      })
      .then((response) => {
        if (response.status == 200) {
          const user: UserProps = {
            pk: response.data.pk,
            first_name: response.data?.first_name ?? '',
            last_name: response.data?.last_name ?? '',
            email: response.data.email,
            username: response.data.username
          };
          set({ user: user });
        } else {
          get().clearUserState();
        }
      })
      .catch(() => {
        get().clearUserState();
      });

    if (!get().isLoggedIn()) {
      return;
    }

    // Fetch role data
    await api
      .get(apiUrl(ApiEndpoints.user_roles))
      .then((response) => {
        if (response.status == 200) {
          const user: UserProps = get().user as UserProps;

          // Update user with role data
          if (user) {
            user.roles = response.data?.roles ?? {};
            user.permissions = response.data?.permissions ?? {};
            user.is_staff = response.data?.is_staff ?? false;
            user.is_superuser = response.data?.is_superuser ?? false;
            set({ user: user });
          }
        } else {
          get().clearUserState();
        }
      })
      .catch((_error) => {
        console.error('ERR: Error fetching user roles');
        get().clearUserState();
      });
  },
  isAuthed: () => {
    return get().is_authed;
  },
  isLoggedIn: () => {
    if (!get().isAuthed()) {
      return false;
    }
    const user: UserProps = get().user as UserProps;
    return !!user && !!user.pk;
  },
  isStaff: () => {
    const user: UserProps = get().user as UserProps;
    return user?.is_staff ?? false;
  },
  isSuperuser: () => {
    const user: UserProps = get().user as UserProps;
    return user?.is_superuser ?? false;
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
  },
  checkUserPermission: (model: ModelType, permission: UserPermissions) => {
    // Check if the user has the specified permission for the specified model
    const user: UserProps = get().user as UserProps;

    if (!user) {
      return false;
    }

    if (user?.is_superuser) return true;

    if (user?.permissions === undefined) return false;
    if (user?.permissions[model] === undefined) return false;
    if (user?.permissions[model] === null) return false;

    return user?.permissions[model]?.includes(permission) ?? false;
  },
  hasDeletePermission: (model: ModelType) => {
    return get().checkUserPermission(model, UserPermissions.delete);
  },
  hasChangePermission: (model: ModelType) => {
    return get().checkUserPermission(model, UserPermissions.change);
  },
  hasAddPermission: (model: ModelType) => {
    return get().checkUserPermission(model, UserPermissions.add);
  },
  hasViewPermission: (model: ModelType) => {
    return get().checkUserPermission(model, UserPermissions.view);
  }
}));
