import type { PluginProps } from '@lib/types/Plugins';
import type { NavigateFunction } from 'react-router-dom';
import { setApiDefaults } from '../App';
import { useServerApiState } from './ApiState';
import { useIconState } from './IconState';
import { useGlobalSettingsState, useUserSettingsState } from './SettingsState';
import { useGlobalStatusState } from './StatusState';
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
  };
}

/*
 * Refetch all global state information.
 * Necessary on login, or if locale is changed.
 */
export async function fetchGlobalStates(
  navigate?: NavigateFunction | undefined
) {
  const { isLoggedIn } = useUserState.getState();

  if (!isLoggedIn()) {
    return;
  }

  setApiDefaults();

  useServerApiState.getState().fetchServerApiState();
  const result = await useUserSettingsState.getState().fetchSettings();
  if (!result && navigate) {
    console.log('MFA is required - setting up');
    // call mfa setup
    navigate('/mfa-setup');
  }
  useGlobalSettingsState.getState().fetchSettings();
  useGlobalStatusState.getState().fetchStatus();
  useIconState.getState().fetchIcons();
}
