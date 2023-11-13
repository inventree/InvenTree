import { Trans, t } from '@lingui/macro';
import { Stack } from '@mantine/core';
import {
  IconBellCog,
  IconDeviceDesktop,
  IconDeviceDesktopAnalytics,
  IconFileAnalytics,
  IconLock,
  IconSearch,
  IconUserCircle
} from '@tabler/icons-react';
import { useMemo } from 'react';

import { PanelGroup, PanelType } from '../../../components/nav/PanelGroup';
import { SettingsHeader } from '../../../components/nav/SettingsHeader';
import { UserSettingList } from '../../../components/settings/SettingList';
import { useUserState } from '../../../states/UserState';
import { SecurityContent } from './AccountSettings/SecurityContent';
import { AccountContent } from './AccountSettings/UserPanel';

/**
 * User settings page
 */
export default function UserSettings() {
  const userSettingsPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'account',
        label: t`Account`,
        icon: <IconUserCircle />,
        content: <AccountContent />
      },
      {
        name: 'security',
        label: t`Security`,
        icon: <IconLock />,
        content: <SecurityContent />
      },
      {
        name: 'dashboard',
        label: t`Dashboard`,
        icon: <IconDeviceDesktopAnalytics />
      },
      {
        name: 'display',
        label: t`Display Options`,
        icon: <IconDeviceDesktop />,
        content: (
          <UserSettingList
            keys={[
              'STICKY_HEADER',
              'DATE_DISPLAY_FORMAT',
              'FORMS_CLOSE_USING_ESCAPE',
              'PART_SHOW_QUANTITY_IN_FORMS',
              'DISPLAY_SCHEDULE_TAB',
              'DISPLAY_STOCKTAKE_TAB',
              'TABLE_STRING_MAX_LENGTH'
            ]}
          />
        )
      },
      {
        name: 'search',
        label: t`Search`,
        icon: <IconSearch />,
        content: (
          <UserSettingList
            keys={[
              'SEARCH_WHOLE',
              'SEARCH_REGEX',
              'SEARCH_PREVIEW_RESULTS',
              'SEARCH_PREVIEW_SHOW_PARTS',
              'SEARCH_HIDE_INACTIVE_PARTS',
              'SEARCH_PREVIEW_SHOW_SUPPLIER_PARTS',
              'SEARCH_PREVIEW_SHOW_MANUFACTURER_PARTS',
              'SEARCH_PREVIEW_SHOW_CATEGORIES',
              'SEARCH_PREVIEW_SHOW_STOCK',
              'SEARCH_PREVIEW_HIDE_UNAVAILABLE_STOCK',
              'SEARCH_PREVIEW_SHOW_LOCATIONS',
              'SEARCH_PREVIEW_SHOW_COMPANIES',
              'SEARCH_PREVIEW_SHOW_BUILD_ORDERS',
              'SEARCH_PREVIEW_SHOW_PURCHASE_ORDERS',
              'SEARCH_PREVIEW_EXCLUDE_INACTIVE_PURCHASE_ORDERS',
              'SEARCH_PREVIEW_SHOW_SALES_ORDERS',
              'SEARCH_PREVIEW_EXCLUDE_INACTIVE_SALES_ORDERS',
              'SEARCH_PREVIEW_SHOW_RETURN_ORDERS',
              'SEARCH_PREVIEW_EXCLUDE_INACTIVE_RETURN_ORDERS'
            ]}
          />
        )
      },
      {
        name: 'notifications',
        label: t`Notifications`,
        icon: <IconBellCog />
      },
      {
        name: 'reporting',
        label: t`Reporting`,
        icon: <IconFileAnalytics />,
        content: (
          <UserSettingList
            keys={['REPORT_INLINE', 'LABEL_INLINE', 'LABEL_DEFAULT_PRINTER']}
          />
        )
      }
    ];
  }, []);
  const [user] = useUserState((state) => [state.user]);

  return (
    <>
      <Stack spacing="xs">
        <SettingsHeader
          title={t`Account Settings`}
          subtitle={`${user?.first_name} ${user?.last_name}`}
          shorthand={user?.username || ''}
          switch_link="/settings/system"
          switch_text={<Trans>Switch to System Setting</Trans>}
          switch_condition={user?.is_staff || false}
        />
        <PanelGroup pageKey="user-settings" panels={userSettingsPanels} />
      </Stack>
    </>
  );
}
