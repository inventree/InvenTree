import { t } from '@lingui/macro';
import { notifications } from '@mantine/notifications';
import {} from '@tabler/icons-react';
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
