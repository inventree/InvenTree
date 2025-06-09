import { ActionIcon, Alert, Group, Menu, Stack, Tooltip } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import { useMemo, useState } from 'react';

import { t } from '@lingui/core/macro';
import { useShallow } from 'zustand/react/shallow';
import { docLinks } from '../../defaults/links';
import { useServerApiState } from '../../states/ApiState';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';

interface AlertInfo {
  key: string;
  title: string;
  code?: string;
  message: string;
  error?: boolean;
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
  const [server] = useServerApiState(useShallow((state) => [state.server]));
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

    if (!server?.email_configured) {
      _alerts.push({
        key: 'email',
        title: t`Email settings`,
        code: 'INVE-W7',
        message: t`Email settings not configured.`
      });
    }

    if (globalSettings.isSet('SERVER_RESTART_REQUIRED')) {
      _alerts.push({
        key: 'restart',
        title: t`Server Restart`,
        code: 'INVE-W6',
        message: t`The server requires a restart to apply changes.`
      });
    }

    const n_migrations =
      Number.parseInt(globalSettings.getSetting('_PENDING_MIGRATIONS')) ?? 0;

    if (n_migrations > 0) {
      _alerts.push({
        key: 'migrations',
        title: t`Database Migrations`,
        code: 'INVE-W8',
        message: t`There are pending database migrations.`
      });
    }

    return _alerts.filter((alert) => !dismissed.includes(alert.key));
  }, [server, dismissed, globalSettings]);

  const anyErrors: boolean = useMemo(
    () => alerts.some((alert) => alert.error),
    [alerts]
  );

  if (user.isStaff() && alerts.length > 0)
    return (
      <Menu withinPortal={true} position='bottom-end'>
        <Menu.Target>
          <Tooltip position='bottom-end' label={t`Alerts`}>
            <ActionIcon
              variant='transparent'
              aria-label='open-alerts'
              color={anyErrors ? 'red' : 'orange'}
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
                color={alert.error ? 'red' : 'orange'}
                title={
                  <Group gap='xs'>
                    {alert.code && `${alert.code}: `}
                    {alert.title}
                  </Group>
                }
                onClose={() => setDismissed([...dismissed, alert.key])}
              >
                <Stack gap='xs'>
                  {alert.message}
                  {alert.code && errorCodeLink(alert.code)}
                </Stack>
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
