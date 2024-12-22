import { t } from '@lingui/macro';
import { Skeleton, Stack } from '@mantine/core';
import {
  IconBellCog,
  IconDeviceDesktop,
  IconFileAnalytics,
  IconLock,
  IconSearch,
  IconUserCircle
} from '@tabler/icons-react';
import { useMemo } from 'react';

import PageTitle from '../../../components/nav/PageTitle';
import { SettingsHeader } from '../../../components/nav/SettingsHeader';
import type { PanelType } from '../../../components/panels/Panel';
import { PanelGroup } from '../../../components/panels/PanelGroup';
import { UserSettingList } from '../../../components/settings/SettingList';
import { useUserState } from '../../../states/UserState';
import { SecurityContent } from './AccountSettings/SecurityContent';
import { AccountContent } from './AccountSettings/UserPanel';

/**
 * User settings page
 */
export default function UserSettings() {
  const [user, isLoggedIn] = useUserState((state) => [
    state.user,
    state.isLoggedIn
  ]);

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
        icon: <IconBellCog />,
        content: <UserSettingList keys={['NOTIFICATION_ERROR_REPORT']} />
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

  if (!isLoggedIn()) {
    return <Skeleton />;
  }

  return (
    <>
      <PageTitle title={t`User Settings`} />
      <Stack gap='xs'>
        <SettingsHeader
          label='user'
          title={t`Account Settings`}
          subtitle={
            user?.first_name && user?.last_name
              ? `${user?.first_name} ${user?.last_name}`
              : null
          }
          shorthand={user?.username || ''}
        />
        <PanelGroup
          pageKey='user-settings'
          panels={userSettingsPanels}
          model='usersettings'
          id={null}
        />
      </Stack>
    </>
  );
}
