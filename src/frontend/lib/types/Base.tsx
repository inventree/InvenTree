import type { MantineSize } from '@mantine/core';
import type React from 'react';

export type UiSizeType = MantineSize | string | number;

// Define a "host" (remote InvenTree server)
export interface Host {
  host: string;
  name: string;
}

export interface HostList {
  [key: string]: Host;
}

// Define interface for user profile
interface UserProfile {
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

export interface UserTheme {
  primaryColor: string;
  whiteColor: string;
  blackColor: string;
  radius: UiSizeType;
  loader: string;
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

// Type interface defining a plugin
export interface PluginProps {
  name: string;
  slug: string;
  version: null | string;
}

declare global {
  interface Window {
    INVENTREE_SETTINGS: {
      server_list: HostList;
      default_server: string;
      show_server_selector: boolean;
      base_url: string;
      sentry_dsn?: string;
      environment?: string;
    };
    React: typeof React;
  }
}
