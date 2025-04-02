import { ActionIcon, Alert, Menu, Tooltip } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import { useMemo, useState } from 'react';

import { t } from '@lingui/core/macro';
import { docLinks } from '../../defaults/links';
import { useServerApiState } from '../../states/ApiState';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';

interface AlertInfo {
  key: string;
  title: string;
  code?: string;
  message: string;
}

/**
 * The `Alerts` component displays a menu of alerts for staff users based on the server state
 * and global settings. Alerts are shown as a dropdown menu with actionable items that can be dismissed.
 *
 * Dismissed alerts are filtered out and will not reappear in the current session.
 *
 * @returns A dropdown menu of alerts for staff users or `null` if there are no alerts or the user is not a staff member.
 */
export function Alerts() {
  const user = useUserState();
  const [server] = useServerApiState((state) => [state.server]);
  const globalSettings = useGlobalSettingsState();

  const [dismissed, setDismissed] = useState<string[]>([]);

  const alerts: AlertInfo[] = useMemo(() => {
    const _alerts: AlertInfo[] = [];

    if (server?.debug_mode) {
      _alerts.push({
        key: 'debug',
        title: t`Debug Mode`,
        code: 'INVE-W4',
        message: t`The server is running in debug mode.`
      });
    }

    if (!server?.worker_running) {
      _alerts.push({
        key: 'worker',
        title: t`Background Worker`,
        code: 'INVE-W5',
        message: t`The background worker process is not running.`
      });
    }

    if (globalSettings.isSet('SERVER_RESTART_REQUIRED')) {
      _alerts.push({
        key: 'restart',
        title: t`Server Restart`,
        message: t`The server requires a restart to apply changes.`
      });
    }

    const n_migrations =
      Number.parseInt(globalSettings.getSetting('_PENDING_MIGRATIONS')) ?? 0;

    if (n_migrations > 0) {
      _alerts.push({
        key: 'migrations',
        title: t`Database Migrations`,
        message: t`There are pending database migrations.`
      });
    }

    return _alerts.filter((alert) => !dismissed.includes(alert.key));
  }, [server, dismissed, globalSettings]);

  if (user.isStaff() && alerts.length > 0)
    return (
      <Menu withinPortal={true} position='bottom-end'>
        <Menu.Target>
          <Tooltip position='bottom-end' label={t`Alerts`}>
            <ActionIcon
              variant='transparent'
              aria-label='open-alerts'
              color='red'
            >
              <IconExclamationCircle />
            </ActionIcon>
          </Tooltip>
        </Menu.Target>
        <Menu.Dropdown>
          {alerts.map((alert) => (
            <Menu.Item key={`alert-item-${alert.key}`}>
              <Alert
                withCloseButton
                color='red'
                title={alert.title}
                onClose={() => setDismissed([...dismissed, alert.key])}
              >
                {alert.message}
                {alert.code && errorCodeLink(alert.code)}
              </Alert>
            </Menu.Item>
          ))}
        </Menu.Dropdown>
      </Menu>
    );
  return null;
}
export function errorCodeLink(code: string) {
  return (
    <a
      href={`${docLinks.errorcodes}#${code.toLowerCase()}`}
      target='_blank'
      rel='noreferrer'
    >
      {t`Learn more about ${code}`}
    </a>
  );
}
