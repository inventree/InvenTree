import { t } from '@lingui/macro';
import { notifications } from '@mantine/notifications';
import {
  IconCircleCheck,
  IconExclamationCircle,
  IconStopwatch
} from '@tabler/icons-react';

/**
 * Show a notification that the user does not have permission to perform the action
 */
export function permissionDenied() {
  notifications.show({
    title: t`Permission Denied`,
    message: t`You do not have permission to perform this action`,
    color: 'red',
    icon: <IconExclamationCircle />
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
    icon: <IconExclamationCircle />,
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
    icon: <IconStopwatch />,
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
