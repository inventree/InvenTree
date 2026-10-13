import { notifications } from '@mantine/notifications';
import { IconCircleCheck, IconExclamationCircle } from '@tabler/icons-react';
import { extractErrorMessage } from './api';

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
  field,
  id
}: {
  error: any;
  title: string;
  message?: string;
  field?: string;
  id?: string;
}) {
  const errorMessage = extractErrorMessage({
    error: error,
    field: field,
    defaultMessage: message
  });

  notifications.hide(id ?? 'api-error');

  notifications.show({
    id: id ?? 'api-error',
    title: title,
    message: errorMessage,
    color: 'red'
  });
}
