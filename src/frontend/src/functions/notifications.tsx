import { t } from '@lingui/macro';
import { notifications } from '@mantine/notifications';

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
