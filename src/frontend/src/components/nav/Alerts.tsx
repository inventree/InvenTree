import { ActionIcon, Alert, Group, Menu, Stack, Tooltip } from '@mantine/core';
import { IconCircleCheck, IconExclamationCircle } from '@tabler/icons-react';
import { useMemo, useState } from 'react';

import type { SettingsStateProps } from '@lib/types/Settings';
import { t } from '@lingui/core/macro';
import { useShallow } from 'zustand/react/shallow';
import { docLinks } from '../../defaults/links';
import { useServerApiState } from '../../states/ServerApiState';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import type { ServerAPIProps } from '../../states/states';

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

  const alerts: ExtendedAlertInfo[] = useMemo(
    () =>
      getAlerts(server, globalSettings).filter(
        (alert) => !dismissed.includes(alert.key)
      ),
    [server, dismissed, globalSettings]
  );

  const anyErrors: boolean = useMemo(
    () => alerts.some((alert) => alert.error),
    [alerts]
  );
  function closeAlert(key: string) {
    setDismissed([...dismissed, key]);
  }

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
              <ServerAlert alert={alert} closeAlert={closeAlert} />
            </Menu.Item>
          ))}
        </Menu.Dropdown>
      </Menu>
    );
  return null;
}

export function ServerAlert({
  alert,
  closeAlert
}: { alert: ExtendedAlertInfo; closeAlert?: (key: string) => void }) {
  return (
    <Alert
      withCloseButton={!!closeAlert}
      color={alert.condition ? (alert.error ? 'red' : 'orange') : 'green'}
      icon={alert.condition ? <IconExclamationCircle /> : <IconCircleCheck />}
      title={
        <Group gap='xs'>
          {alert.code && `${alert.code}: `}
          {alert.title}
        </Group>
      }
      onClose={closeAlert ? () => closeAlert(alert.key) : undefined}
    >
      <Stack gap='xs'>
        {!alert.condition && t`No issues detected`}
        {alert.condition && alert.message}
        {alert.condition && alert.code && errorCodeLink(alert.code)}
      </Stack>
    </Alert>
  );
}

export type ExtendedAlertInfo = AlertInfo & {
  condition: boolean;
};

export function getAlerts(
  server: ServerAPIProps,
  globalSettings: SettingsStateProps,
  inactive = false
): ExtendedAlertInfo[] {
  const n_migrations =
    Number.parseInt(globalSettings.getSetting('_PENDING_MIGRATIONS')) ?? 0;

  const allAlerts: ExtendedAlertInfo[] = [
    {
      key: 'debug',
      title: t`Debug Mode`,
      code: 'INVE-W4',
      message: t`The server is running in debug mode.`,
      condition: server?.debug_mode || false
    },
    {
      key: 'worker',
      title: t`Background Worker`,
      code: 'INVE-W5',
      message: t`The background worker process is not running.`,
      condition: !server?.worker_running
    },
    {
      key: 'restart',
      title: t`Server Restart`,
      code: 'INVE-W6',
      message: t`The server requires a restart to apply changes.`,
      condition: globalSettings.isSet('SERVER_RESTART_REQUIRED')
    },
    {
      key: 'email',
      title: t`Email settings`,
      code: 'INVE-W7',
      message: t`Email settings not configured.`,
      condition: !server?.email_configured
    },
    {
      key: 'migrations',
      title: t`Database Migrations`,
      code: 'INVE-W8',
      message: t`There are pending database migrations.`,
      condition: n_migrations > 0
    }
  ];

  return allAlerts.filter((alert) => inactive || alert.condition);
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
