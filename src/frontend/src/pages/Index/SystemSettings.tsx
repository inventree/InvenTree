import { t } from '@lingui/macro';
import { Divider, Stack } from '@mantine/core';
import {
  IconBellCog,
  IconCategory,
  IconClipboardCheck,
  IconCurrencyDollar,
  IconFileAnalytics,
  IconFingerprint,
  IconList,
  IconListDetails,
  IconPackages,
  IconQrcode,
  IconScale,
  IconServerCog,
  IconShoppingCart,
  IconSitemap,
  IconTag,
  IconTools,
  IconTruckDelivery
} from '@tabler/icons-react';
import { useMemo } from 'react';

import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup, PanelType } from '../../components/nav/PanelGroup';
import { SettingList } from '../../components/settings/SettingList';
import { ProjectCodeTable } from '../../components/tables/settings/ProjectCodeTable';
import { ApiPaths, url } from '../../states/ApiState';
import { useGlobalSettingsState } from '../../states/SettingsState';

/**
 * System settings page
 */
export default function SystemSettings() {
  const globalSettings = useGlobalSettingsState();

  const systemSettingsPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'server',
        label: t`Server`,
        icon: <IconServerCog />,
        content: (
          <SettingList
            settingsState={globalSettings}
            keys={[
              'INVENTREE_BASE_URL',
              'INVENTREE_COMPANY_NAME',
              'INVENTREE_INSTANCE',
              'INVENTREE_INSTANCE_TITLE',
              'INVENTREE_RESTRICT_ABOUT',
              'INVENTREE_UPDATE_CHECK_INTERVAL',
              'INVENTREE_DOWNLOAD_FROM_URL',
              'INVENTREE_DOWNLOAD_IMAGE_MAX_SIZE',
              'INVENTREE_DOWNLOAD_FROM_URL_USER_AGENT',
              'INVENTREE_REQUIRE_CONFIRM',
              'INVENTREE_TREE_DEPTH',
              'INVENTREE_BACKUP_ENABLE',
              'INVENTREE_BACKUP_DAYS',
              'INVENTREE_DELETE_TASKS_DAYS',
              'INVENTREE_DELETE_ERRORS_DAYS',
              'INVENTREE_DELETE_NOTIFICATIONS_DAYS'
            ]}
          />
        )
      },
      {
        name: 'login',
        label: t`Login`,
        icon: <IconFingerprint />,
        content: (
          <SettingList
            settingsState={globalSettings}
            keys={[
              'LOGIN_ENABLE_PWD_FORGOT',
              'LOGIN_MAIL_REQUIRED',
              'LOGIN_ENFORCE_MFA',
              'LOGIN_ENABLE_REG',
              'LOGIN_SIGNUP_MAIL_TWICE',
              'LOGIN_SIGNUP_PWD_TWICE',
              'SIGNUP_GROUP',
              'LOGIN_SIGNUP_MAIL_RESTRICTION',
              'LOGIN_ENABLE_SSO',
              'LOGIN_ENABLE_SSO_REG',
              'LOGIN_SIGNUP_SSO_AUTO'
            ]}
          />
        )
      },
      {
        name: 'barcode',
        label: t`Barcodes`,
        icon: <IconQrcode />,
        content: (
          <SettingList
            settingsState={globalSettings}
            keys={[
              'BARCODE_ENABLE',
              'BARCODE_INPUT_DELAY',
              'BARCODE_WEBCAM_SUPPORT'
            ]}
          />
        )
      },
      {
        name: 'projectcodes',
        label: t`Project Codes`,
        icon: <IconListDetails />,
        content: (
          <Stack spacing="xs">
            <SettingList
              settingsState={globalSettings}
              keys={['PROJECT_CODES_ENABLED']}
            />
            <Divider />
            <ProjectCodeTable />
          </Stack>
        )
      },
      {
        name: 'physicalunits',
        label: t`Physical Units`,
        icon: <IconScale />
      },
      {
        name: 'notifications',
        label: t`Notifications`,
        icon: <IconBellCog />
      },
      {
        name: 'pricing',
        label: t`Pricing`,
        icon: <IconCurrencyDollar />
      },
      {
        name: 'labels',
        label: t`Labels`,
        icon: <IconTag />,
        content: (
          <SettingList
            settingsState={globalSettings}
            keys={['LABEL_ENABLE', 'LABEL_DPI']}
          />
        )
      },
      {
        name: 'reporting',
        label: t`Reporting`,
        icon: <IconFileAnalytics />,
        content: (
          <SettingList
            settingsState={globalSettings}
            keys={[
              'REPORT_ENABLE',
              'REPORT_DEFAULT_PAGE_SIZE',
              'REPORT_DEBUG_MODE',
              'REPORT_ENABLE_TEST_REPORT',
              'REPORT_ATTACH_TEST_REPORT'
            ]}
          />
        )
      },
      {
        name: 'categories',
        label: t`Part Categories`,
        icon: <IconSitemap />
      },
      {
        name: 'parts',
        label: t`Parts`,
        icon: <IconCategory />,
        content: <SettingList settingsState={globalSettings} keys={[]} />
      },
      {
        name: 'parameters',
        label: t`Part Parameters`,
        icon: <IconList />
      },
      {
        name: 'stock',
        label: t`Stock`,
        icon: <IconPackages />,
        content: (
          <SettingList
            settingsState={globalSettings}
            keys={[
              'SERIAL_NUMBER_GLOBALLY_UNIQUE',
              'SERIAL_NUMBER_AUTOFILL',
              'STOCK_DELETE_DEPLETED_DEFAULT',
              'STOCK_BATCH_CODE_TEMPLATE',
              'STOCK_ENABLE_EXPIRY',
              'STOCK_STALE_DAYS',
              'STOCK_ALLOW_EXPIRED_SALE',
              'STOCK_ALLOW_EXPIRED_BUILD',
              'STOCK_OWNERSHIP_CONTROL',
              'STOCK_LOCATION_DEFAULT_ICON',
              'STOCK_SHOW_INSTALLED_ITEMS'
            ]}
          />
        )
      },
      {
        name: 'stocktake',
        label: t`Stocktake`,
        icon: <IconClipboardCheck />
      },
      {
        name: 'buildorders',
        label: t`Build Orders`,
        icon: <IconTools />,
        content: (
          <SettingList
            settingsState={globalSettings}
            keys={['BUILDORDER_REFERENCE_PATTERN']}
          />
        )
      },
      {
        name: 'purchaseorders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart />,
        content: (
          <SettingList
            settingsState={globalSettings}
            keys={[
              'PURCHASEORDER_REFERENCE_PATTERN',
              'PURCHASEORDER_EDIT_COMPLETED_ORDERS'
            ]}
          />
        )
      },
      {
        name: 'salesorders',
        label: t`Sales Orders`,
        icon: <IconTruckDelivery />,
        content: (
          <SettingList
            settingsState={globalSettings}
            keys={[
              'SALESORDER_REFERENCE_PATTERN',
              'SALESORDER_DEFAULT_SHIPMENT',
              'SALESORDER_EDIT_COMPLETED_ORDERS'
            ]}
          />
        )
      }
    ];
  }, []);

  return (
    <>
      <Stack spacing="xs">
        <PageDetail title={t`System Settings`} />
        <PanelGroup panels={systemSettingsPanels} />
      </Stack>
    </>
  );
}
