export interface Profile {
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
  profile: Profile;
}
