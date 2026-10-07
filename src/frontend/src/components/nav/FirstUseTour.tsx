import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Tour } from '@mantine/core';
import { Button, Group, Text, rem } from '@mantine/core';
import { type NotificationData, notifications } from '@mantine/notifications';
import { type Dispatch, type SetStateAction, useEffect, useState } from 'react';
import { useUserState } from '../../states/UserState';

const ftusteps = [
  {
    target: 'tipp-ftu-search',
    title: t`Search`,
    description: t`Click the beacon to see this tooltip.`
  },
  {
    target: 'tipp-ftu-cmd',
    title: t`Command Palette`,
    description: t`This is the second beacon tooltip.`
  },
  {
    target: 'tipp-ftu-barcode',
    title: t`Barcode Scanner`,
    description: t`This is the second "a" beacon tooltip.`
  },
  {
    target: 'tipp-ftu-notif',
    title: t`Notifications`,
    description: t`This is the third beacon tooltip.`
  },
  {
    target: 'tipp-ftu-nav1',
    title: t`Navigation Area`,
    description: t`This is the fourth beacon tooltip.`
  },
  {
    target: 'tipp-ftu-nav2',
    title: t`Navigation Drawer`,
    description: t`This is the fifth beacon tooltip.`
  },
  {
    target: 'tipp-ftu-nav3',
    title: t`Main Menu`,
    description: t`This is the sixth beacon tooltip.`
  }
];

export function FirstUseTour() {
  const { user } = useUserState();
  const hasCompletedFtu = user?.profile?.widgets?.includes('ftue') ?? false;
  const [active, setActive] = useState(false);
  const [notificationId, setNotificationId] = useState<string | null>(null);

  if (!user || hasCompletedFtu) {
    return null;
  }

  // show notif to nudge the user to complete the First Use Tour
  useEffect(() => {
    if (!active && !notificationId) {
      const id = notifications.show({
        autoClose: false,
        renderNotification: (notification) =>
          ftuNotification(setActive, notification),
        message: ''
      });
      setNotificationId(id);
    }
  }, []);

  return (
    <Tour
      active={active}
      onClose={() => {
        // TODO update backend
        setActive(false);
      }}
    >
      {ftusteps.map((step, index) => (
        <Tour.Step key={index} target={`#${step.target}`} title={step.title}>
          {step.description}
        </Tour.Step>
      ))}
    </Tour>
  );
}

function ftuNotification(
  setActive: Dispatch<SetStateAction<boolean>>,
  notification: NotificationData
): import('react').ReactNode {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: rem(12),
        padding: rem(16),
        backgroundColor: 'var(--mantine-color-body)',
        border: '1px solid var(--mantine-color-default-border)',
        userSelect: 'none'
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <Text size='sm' fw={600}>
          <Trans>First Use Tour available</Trans>
        </Text>
        <Text size='xs' c='dimmed' lineClamp={1}>
          <Trans>
            It looks like you did not complete the First Use Tour yet.
          </Trans>
        </Text>
        <Group gap='xs' mt={8}>
          <Button
            size='compact-xs'
            variant='filled'
            onClick={() => {
              // TODO update backend
              setActive(true);
              notifications.hide(notification.id!);
            }}
          >
            <Trans>Start Tour</Trans>
          </Button>
          <Button
            size='compact-xs'
            variant='default'
            c='red'
            onClick={() => {
              // TODO update backend
              setActive(false);
              notifications.hide(notification.id!);
            }}
          >
            <Trans>Dismiss permanently</Trans>
          </Button>
        </Group>
      </div>
    </div>
  );
}
