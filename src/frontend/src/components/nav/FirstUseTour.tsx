import { ApiEndpoints, apiUrl } from '@lib/index';
import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Button, Group, Text, Tour, rem } from '@mantine/core';
import { useWindowEvent } from '@mantine/hooks';
import { type NotificationData, notifications } from '@mantine/notifications';

import {
  type Dispatch,
  type SetStateAction,
  useEffect,
  useMemo,
  useState
} from 'react';
import { api } from '../../App';
import { useServerApiState } from '../../states/ServerApiState';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';

interface FtuStep {
  target: string;
  title: string;
  description: string;
  action_before?: () => void;
}

const ftuKex = 'org.inventree.i.tipp.ftue';

export function FirstUseTour() {
  const { user, done_tipps, setTipps } = useUserState();
  const hasCompletedFtu = done_tipps?.includes(ftuKex) ?? false;
  const [active, setActive] = useState(false);
  const globalSettings = useGlobalSettingsState();
  const userSettings = useUserSettingsState();
  const { ftuShown, setFtuShown } = useServerApiState();
  const showNudge = !!user && !hasCompletedFtu;

  const ftusteps = useMemo(() => {
    const _steps: FtuStep[] = [
      {
        target: 'tipp-ftu-nav1',
        title: t`Navigation Area`,
        description: t`The navigation area provides quick access to different sections of the application.`
      },
      {
        target: 'tipp-ftu-nav2',
        title: t`Navigation Drawer`,
        description: t`Using the icon you can open and close the navigation drawer which contains most available pages accessible to you.`
      },
      {
        target: 'tipp-ftu-nav3',
        title: t`Main Menu`,
        description: t`The main menu provides access to top level navigation targets. Plugins can extend the menu with additional options.`
      },
      {
        target: 'tipp-ftu-search',
        title: t`Search`,
        description: t`The global search allows you to quickly find items across all objects. You can configure which objects categories are included in the search and how terms are matched.`
      }
    ];
    if (userSettings.isSet('SHOW_SPOTLIGHT')) {
      _steps.push({
        target: 'tipp-ftu-cmd',
        title: t`Command Palette`,
        description: t`Quickly access commands and actions anywhere using the command palette. Available commands are dependent on your current context. Use cmd + k to open it anywhere.`
      });
    }

    if (globalSettings.isSet('BARCODE_ENABLE')) {
      _steps.push({
        target: 'tipp-ftu-barcode',
        title: t`Barcode Scanner`,
        description: t`Allows for quick scanning of barcodes with your device's camera or a handheld scanner.`
      });
    }

    _steps.push(
      {
        target: 'tipp-ftu-notif',
        title: t`Notifications`,
        description: t`Depending on your instance and user settings notifications are delivered through various channels. This notification bar is annotated with a bell when there are unread user interface notifications.`
      },
      {
        target: 'tipp-ftu-settings',
        title: t`Settings`,
        description: t`The main menu allows you to access preferences and access system-wide settings. Options depend on your permissions.`,
        action_before: () => {
          window.dispatchEvent(new Event('inventree:open-main-menu'));
        }
      },
      {
        target: 'tipp-ftu-usersettings',
        title: t`User Settings`,
        description: t`The user settings menu allows you to configure your personal preferences and account settings. This also contains security and notification settings.`
      }
    );

    if (user?.is_staff) {
      _steps.push({
        target: 'tipp-ftu-admincenter',
        title: t`Admin Center`,
        description: t`The admin center provides access to administrative functions and can be used to manage various functions required for operation of the instance like user management, templates, parameters, plugins.`
      });
    }

    _steps.push({
      target: 'tipp-ftu-about',
      title: t`About InvenTree`,
      description: t`Provides information about the InvenTree instance, including version details and relevant links. Important for bug reports.`
    });
    return _steps;
  }, [userSettings, globalSettings]);

  const completeTour = () => {
    setActive(false);
    window.dispatchEvent(new Event('inventree:close-main-menu'));

    if (!user) return;
    const tipp_pk = user.tipps?.find((tipp) => tipp.tipp_id === ftuKex)?.pk;
    if (!tipp_pk) return;
    api
      .patch(apiUrl(ApiEndpoints.user_me_tipps, tipp_pk), { finished: true })
      .then((result) => {
        setTipps(
          user.tipps?.map((tipp) =>
            tipp.pk === tipp_pk ? result.data : tipp
          ) ?? null
        );
      });
  };

  useWindowEvent('inventree:start-ftu', () => setActive(true));

  // show notif to nudge the user to complete the First Use Tour
  useEffect(() => {
    if (showNudge && !active) {
      // session deduplication
      if (ftuShown) return;
      setFtuShown(true);

      notifications.show({
        autoClose: false,
        renderNotification: (notification) =>
          ftuNotification(setActive, completeTour, notification),
        message: ''
      });
    }
  }, [showNudge]);

  // rendering
  if (!user) {
    return null;
  }
  return (
    <Tour active={active} onClose={completeTour} zIndex={10002}>
      {ftusteps.map((step, index) => (
        <Tour.Step
          key={index}
          target={`#${step.target}`}
          title={step.title}
          onStepOpen={step.action_before}
        >
          {step.description}
        </Tour.Step>
      ))}
    </Tour>
  );
}

function ftuNotification(
  setActive: Dispatch<SetStateAction<boolean>>,
  completeTour: () => void,
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
              setActive(false);
              notifications.hide(notification.id!);

              completeTour();
            }}
          >
            <Trans>Dismiss permanently</Trans>
          </Button>
        </Group>
      </div>
    </div>
  );
}
