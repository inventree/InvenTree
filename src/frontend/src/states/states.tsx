import { setApiDefaults } from '../App';
import { useServerApiState } from './ApiState';
import { useIconState } from './IconState';
import { useGlobalSettingsState, useUserSettingsState } from './SettingsState';
import { useGlobalStatusState } from './StatusState';
import { useUserState } from './UserState';

export interface Host {
  host: string;
  name: string;
}

export interface HostList {
  [key: string]: Host;
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
}

// Type interface fully defining the current server
export interface ServerAPIProps {
  server: null | string;
  version: null | string;
  instance: null | string;
  apiVersion: null | number;
  worker_running: null | boolean;
  worker_pending_tasks: null | number;
  plugins_enabled: null | boolean;
  plugins_install_disabled: null | boolean;
  active_plugins: PluginProps[];
  email_configured: null | boolean;
  debug_mode: null | boolean;
  docker_mode: null | boolean;
  database: null | string;
  system_health: null | boolean;
  platform: null | string;
  installer: null | string;
  target: null | string;
  default_locale: null | string;
  django_admin: null | string;
}

export interface AuthProps {
  sso_enabled: boolean;
  sso_registration: boolean;
  mfa_required: boolean;
  providers: Provider[];
  registration_enabled: boolean;
  password_forgotten_enabled: boolean;
}

export interface Provider {
  id: string;
  name: string;
  configured: boolean;
  login: string;
  connect: string;
  display_name: string;
}

// Type interface defining a single 'setting' object
export interface Setting {
  pk: number;
  key: string;
  value: string;
  name: string;
  description: string;
  type: SettingType;
  units: string;
  choices: SettingChoice[];
  model_name: string | null;
  api_url: string | null;
  typ: SettingTyp;
  plugin?: string;
  method?: string;
  required?: boolean;
}

export interface SettingChoice {
  value: string;
  display_name: string;
}

export enum SettingTyp {
  InvenTree = 'inventree',
  Plugin = 'plugin',
  User = 'user',
  Notification = 'notification'
}

export enum SettingType {
  Boolean = 'boolean',
  Integer = 'integer',
  String = 'string',
  Choice = 'choice',
  Model = 'related field'
}

export interface PluginProps {
  name: string;
  slug: string;
  version: null | string;
}

// Errors
export type ErrorResponse = {
  data: any;
  status: number;
  statusText: string;
  message?: string;
};
export type SettingsLookup = {
  [key: string]: string;
};

/*
 * Refetch all global state information.
 * Necessary on login, or if locale is changed.
 */
export function fetchGlobalStates() {
  const { isLoggedIn } = useUserState.getState();

  if (!isLoggedIn()) {
    return;
  }

  setApiDefaults();

  useServerApiState.getState().fetchServerApiState();
  useUserSettingsState.getState().fetchSettings();
  useGlobalSettingsState.getState().fetchSettings();
  useGlobalStatusState.getState().fetchStatus();
  useIconState.getState().fetchIcons();
}
