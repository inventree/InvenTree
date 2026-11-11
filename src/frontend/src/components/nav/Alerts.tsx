import {
  ActionIcon,
  Alert,
  Group,
  Menu,
  Stack,
  Text,
  Tooltip
} from '@mantine/core';
import {
  IconAlertTriangle,
  IconArrowRight,
  IconCircleCheck,
  IconExclamationCircle,
  IconInfoCircle,
  IconListDetails
} from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { t } from '@lingui/core/macro';
import { docLinks } from '../../defaults/links';
import {
  ACTIONABLE_CLASSIFIERS,
  type AdminMessage,
  type AdminMessageClassifier,
  classifierColor,
  useAdminMessages
} from '../../hooks/UseAdminMessages';

/**
 * The `Alerts` component displays a menu of alerts for staff users, based on the
 * system messages provided by the server (via the /api/system/status/ endpoint).
 *
 * Only actionable messages (errors and warnings) are displayed here.
 * Dismissed alerts are filtered out and will not reappear in the current session.
 *
 * @returns A dropdown menu of alerts for staff users or `null` if there are no alerts or the user is not a staff member.
 */
export function Alerts() {
  const { messages } = useAdminMessages();

  const [dismissed, setDismissed] = useState<string[]>([]);

  const alerts: AdminMessage[] = useMemo(
    () =>
      messages.filter(
        (msg) =>
          ACTIONABLE_CLASSIFIERS.includes(msg.classifier) &&
          !dismissed.includes(msg.key)
      ),
    [messages, dismissed]
  );

  const anyErrors: boolean = useMemo(
    () => alerts.some((alert) => alert.classifier === 'error'),
    [alerts]
  );

  function closeAlert(key: string) {
    setDismissed([...dismissed, key]);
  }

  if (alerts.length > 0)
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
          <Menu.Divider />
          <Menu.Item
            component={Link}
            to='/settings/admin/home'
            aria-label='alerts-view-all'
            leftSection={<IconListDetails size={16} />}
            rightSection={<IconArrowRight size={16} />}
          >
            <Text size='md'>{t`View all messages`}</Text>
          </Menu.Item>
        </Menu.Dropdown>
      </Menu>
    );
  return null;
}

function classifierIcon(classifier: AdminMessageClassifier) {
  switch (classifier) {
    case 'error':
      return <IconExclamationCircle />;
    case 'warning':
      return <IconAlertTriangle />;
    case 'info':
      return <IconInfoCircle />;
    case 'success':
    default:
      return <IconCircleCheck />;
  }
}

export function ServerAlert({
  alert,
  closeAlert
}: { alert: AdminMessage; closeAlert?: (key: string) => void }) {
  const actionable = ACTIONABLE_CLASSIFIERS.includes(alert.classifier);

  return (
    <Alert
      withCloseButton={!!closeAlert}
      color={classifierColor(alert.classifier)}
      icon={classifierIcon(alert.classifier)}
      title={
        <Group gap='xs'>
          {alert.code && `${alert.code}: `}
          {alert.title}
        </Group>
      }
      onClose={closeAlert ? () => closeAlert(alert.key) : undefined}
    >
      <Stack gap='xs'>
        {alert.message}
        {actionable && alert.code && errorCodeLink(alert.code)}
      </Stack>
    </Alert>
  );
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
