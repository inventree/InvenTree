import { t } from '@lingui/macro';
import { notifications } from '@mantine/notifications';
import { IconCircleCheck, IconExclamationCircle } from '@tabler/icons-react';
import { extractErrorMessage } from './api';

/**
 * Show a notification that the feature is not yet implemented
 */
export function notYetImplemented() {
  notifications.hide('not-implemented');

  notifications.show({
    title: t`Not implemented`,
    message: t`This feature is not yet implemented`,
    color: 'red',
    id: 'not-implemented'
  });
}

/**
 * Show a notification that the user does not have permission to perform the action
 */
export function permissionDenied() {
  notifications.show({
    title: t`Permission Denied`,
    message: t`You do not have permission to perform this action`,
    color: 'red'
  });
}

/**
 * Display a notification on an invalid return code
 */
export function invalidResponse(returnCode: number) {
  // TODO: Specific return code messages
  notifications.show({
    title: t`Invalid Return Code`,
    message: t`Server returned status ${returnCode}`,
    color: 'red'
  });
}

/**
 * Display a notification on timeout
 */
export function showTimeoutNotification() {
  notifications.show({
    title: t`Timeout`,
    message: t`The request timed out`,
    color: 'red'
  });
}

/*
 * Display a login / logout notification message.
 * Any existing login notification(s) will be hidden.
 */
export function showLoginNotification({
  title,
  message,
  success = true
}: {
  title: string;
  message: string;
  success?: boolean;
}) {
  notifications.hide('login');

  notifications.show({
    title: title,
    message: message,
    color: success ? 'green' : 'red',
    icon: success ? <IconCircleCheck /> : <IconExclamationCircle />,
    id: 'login',
    autoClose: 2500
  });
}

export function showApiErrorMessage({
  error,
  title,
  message,
  field
}: {
  error: any;
  title: string;
  message?: string;
  field?: string;
}) {
  const errorMessage = extractErrorMessage({
    error: error,
    field: field,
    defaultMessage: message
  });

  notifications.show({
    title: title,
    message: errorMessage,
    color: 'red'
  });
}
