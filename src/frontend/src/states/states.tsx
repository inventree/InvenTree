import type { PluginProps } from '@lib/types/Plugins';
import { removeTraceId, setApiDefaults, setTraceId } from '../App';
import { useGlobalStatusState } from './GlobalStatusState';
import { useIconState } from './IconState';
import { useServerApiState } from './ServerApiState';
import { useGlobalSettingsState, useUserSettingsState } from './SettingsStates';
import { useUserState } from './UserState';

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
  settings: {
    sso_registration: null | boolean;
    registration_enabled: null | boolean;
    password_forgotten_enabled: null | boolean;
  } | null;
  customize: null | {
    logo: string;
    splash: string;
    login_message: string;
    navbar_message: string;
    disable_theme_storage: boolean;
  };
}

/*
 * Refetch all global state information.
 * Necessary on login, or if locale is changed.
 */
export async function fetchGlobalStates() {
  const { isLoggedIn } = useUserState.getState();

  if (!isLoggedIn()) {
    return;
  }

  setApiDefaults();
  const traceId = setTraceId();
  await Promise.all([
    useServerApiState.getState().fetchServerApiState(),
    useUserSettingsState.getState().fetchSettings(),
    useGlobalSettingsState.getState().fetchSettings(),
    useGlobalStatusState.getState().fetchStatus(),
    useIconState.getState().fetchIcons()
  ]);
  removeTraceId(traceId);
}
