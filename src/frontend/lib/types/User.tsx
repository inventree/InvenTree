import type { ModelType } from '../enums/ModelType';
import type { UserPermissions, UserRoles } from '../enums/Roles';

export interface UserProfile {
  language: string;
  theme: any;
  widgets: any;
  displayname: string | null;
  position: string | null;
  status: string | null;
  location: string | null;
  active: boolean;
  contact: string | null;
  type: string;
  organisation: string | null;
  primary_group: number | null;
}

// Type interface fully defining the current user
export interface UserProps {
  pk: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  is_staff?: boolean;
  is_superuser?: boolean;
  roles?: Record<string, string[]>;
  permissions?: Record<string, string[]>;
  groups: any[] | null;
  profile: UserProfile;
}

export interface UserStateProps {
  user: UserProps | undefined;
  is_authed: boolean;
  userId: () => number | undefined;
  username: () => string;
  setAuthenticated: (authed?: boolean) => void;
  fetchUserToken: () => Promise<void>;
  setUser: (newUser: UserProps | undefined) => void;
  getUser: () => UserProps | undefined;
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
  // login state
  login_checked: boolean;
  setLoginChecked: (value: boolean) => void;
}
