import { t } from '@lingui/macro';
import { notifications } from '@mantine/notifications';
import { IconCircleCheck, IconExclamationCircle } from '@tabler/icons-react';

/**
 * Show a notification that the feature is not yet implemented
 */
export function notYetImplemented() {
  notifications.show({
    title: t`Not implemented`,
    message: t`This feature is not yet implemented`,
    color: 'red'
  });
}

/**
 * Show a notification that the user does not have permission to perform the action
 */
export function permissionDenied() {
  notifications.show({
    title: t`Permission denied`,
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
    autoClose: 5000
  });
}
