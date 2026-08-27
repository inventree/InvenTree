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

let pendingGlobalStatesFetch: Promise<void> | null = null;
let globalStatesFetched = false;

/*
 * Refetch all global state information.
 * Necessary on login, or if locale is changed.
 *
 * Calls are deduplicated: a call made while a fetch is already in flight
 * reuses that fetch instead of starting another, and once a fetch has
 * completed successfully, later calls are skipped entirely unless `force`
 * is set. Pass `force` when the caller already knows the data needs to be
 * current (an actual login, or a genuine locale change) - other callers
 * (e.g. a page-load auth check that may run after the locale has already
 * triggered a fetch) can rely on the default to avoid redundant requests.
 */
export async function fetchGlobalStates(force = false) {
  const { isLoggedIn } = useUserState.getState();

  if (!isLoggedIn()) {
    return;
  }

  if (pendingGlobalStatesFetch) {
    return pendingGlobalStatesFetch;
  }

  if (globalStatesFetched && !force) {
    return;
  }

  pendingGlobalStatesFetch = (async () => {
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
    globalStatesFetched = true;
  })();

  try {
    await pendingGlobalStatesFetch;
  } finally {
    pendingGlobalStatesFetch = null;
  }
}

/*
 * Reset the "already fetched" guard on fetchGlobalStates, so that the next
 * call performs a real fetch even without `force`. Call this on logout so a
 * subsequent login within the same page session (no full reload) refetches.
 */
export function resetGlobalStatesFetched() {
  globalStatesFetched = false;
}
