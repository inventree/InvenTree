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
