import { t } from '@lingui/macro';
import { Stack } from '@mantine/core';
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
import { InvenTreeSettingsContext } from '../../contexts/SettingsContext';
import { ApiPaths, url } from '../../states/ApiState';

/**
 * System settings page
 */
export default function SystemSettings() {
  const systemSettingsPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'server',
        label: t`Server`,
        icon: <IconServerCog />
      },
      {
        name: 'login',
        label: t`Login`,
        icon: <IconFingerprint />,
        content: (
          <SettingList
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
        icon: <IconListDetails />
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
        content: <SettingList keys={['LABEL_ENABLE', 'LABEL_DPI']} />
      },
      {
        name: 'reporting',
        label: t`Reporting`,
        icon: <IconFileAnalytics />,
        content: (
          <SettingList
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
        content: <SettingList keys={[]} />
      },
      {
        name: 'parameters',
        label: t`Part Parameters`,
        icon: <IconList />
      },
      {
        name: 'stock',
        label: t`Stock`,
        icon: <IconPackages />
      },
      {
        name: 'stocktake',
        label: t`Stocktake`,
        icon: <IconClipboardCheck />
      },
      {
        name: 'buildorders',
        label: t`Build Orders`,
        icon: <IconTools />
      },
      {
        name: 'purchaseorders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart />
      },
      {
        name: 'salesorders',
        label: t`Sales Orders`,
        icon: <IconTruckDelivery />
      }
    ];
  }, []);

  return (
    <>
      <InvenTreeSettingsContext url={url(ApiPaths.settings_global)}>
        <Stack spacing="xs">
          <PageDetail title={t`System Settings`} />
          <PanelGroup panels={systemSettingsPanels} />
        </Stack>
      </InvenTreeSettingsContext>
    </>
  );
}
