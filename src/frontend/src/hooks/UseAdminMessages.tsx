import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { t } from '@lingui/core/macro';
import { useQuery } from '@tanstack/react-query';
import { api } from '../App';
import { useUserState } from '../states/UserState';

export type AdminMessageClassifier = 'error' | 'warning' | 'info' | 'success';

/**
 * A staff-only system message, as returned in the `messages` array of the /api/system/status/ endpoint.
 */
export interface AdminMessage {
  key: string;
  title: string;
  message: string;
  classifier: AdminMessageClassifier;
  code?: string | null;
  plugin?: string | null;
}

/**
 * Staff-only server deployment information,
 * as returned in the `server` object of the /api/system/status/ endpoint.
 */
export interface SystemStatusServerInfo {
  worker_running: boolean;
  worker_count: number;
  worker_pending_tasks: number;
  plugins_install_disabled: boolean;
  email_configured: boolean;
  debug_mode: boolean;
  docker_mode: boolean;
  database: string;
  platform: string;
  installer: string | null;
  target: string | null;
  django_admin: string | null;
}

/** Response format of the /api/system/status/ endpoint */
export interface SystemStatusResponse {
  messages: AdminMessage[];
  server: SystemStatusServerInfo;
}

/** All classifiers, ordered most severe first */
export const ADMIN_MESSAGE_CLASSIFIERS: AdminMessageClassifier[] = [
  'error',
  'warning',
  'info',
  'success'
];

/** Classifiers which indicate that the administrator should take action */
export const ACTIONABLE_CLASSIFIERS: AdminMessageClassifier[] = [
  'error',
  'warning'
];

export function classifierColor(classifier: AdminMessageClassifier): string {
  switch (classifier) {
    case 'error':
      return 'red';
    case 'warning':
      return 'orange';
    case 'info':
      return 'blue';
    case 'success':
    default:
      return 'green';
  }
}

export function classifierLabel(classifier: AdminMessageClassifier): string {
  switch (classifier) {
    case 'error':
      return t`Error`;
    case 'warning':
      return t`Warning`;
    case 'info':
      return t`Info`;
    case 'success':
    default:
      return t`Success`;
  }
}

/**
 * Fetch staff-only system status information from the server.
 * The query is only enabled for staff users (the endpoint is staff-only),
 * so `server` is always undefined for non-staff users.
 */
export function useSystemStatus() {
  const user = useUserState();
  const isStaff = user.isStaff();

  const query = useQuery<SystemStatusResponse | null>({
    enabled: isStaff,
    queryKey: ['system-status', user.userId()],
    // System state changes infrequently, and checks may hit the database
    staleTime: 60 * 1000,
    refetchOnWindowFocus: false,
    queryFn: async () =>
      api
        .get(apiUrl(ApiEndpoints.system_status))
        .then((response) => response.data ?? null)
  });

  const data = isStaff ? (query.data ?? undefined) : undefined;

  return {
    ...query,
    messages: data?.messages ?? [],
    server: data?.server
  };
}

/**
 * Fetch the list of staff-only system messages from the server.
 */
export function useAdminMessages() {
  return useSystemStatus();
}
