import { t } from '@lingui/macro';
import { LoadingOverlay, Stack } from '@mantine/core';
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
import { useInstance } from '../../hooks/UseInstance';
import { ApiPaths, url } from '../../states/ApiState';

/**
 * System settings page
 */
export default function SystemSettings() {
  // Query manager for global system settings
  const {
    instance: settings,
    refreshInstance: reloadSettings,
    instanceQuery: settingsQuery
  } = useInstance({
    url: url(ApiPaths.settings_global),
    hasPrimaryKey: false,
    fetchOnMount: true,
    defaultValue: []
  });

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
        icon: <IconFingerprint />
      },
      {
        name: 'barcode',
        label: t`Barcodes`,
        icon: <IconQrcode />
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
        icon: <IconTag />
      },
      {
        name: 'reporting',
        label: t`Reporting`,
        icon: <IconFileAnalytics />
      },
      {
        name: 'categories',
        label: t`Part Categories`,
        icon: <IconSitemap />
      },
      {
        name: 'parts',
        label: t`Parts`,
        icon: <IconCategory />
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
  }, [settings]);

  return (
    <>
      <Stack spacing="xs">
        <LoadingOverlay visible={settingsQuery.isFetching} />
        <PageDetail title={t`System Settings`} />
        <PanelGroup panels={systemSettingsPanels} />
      </Stack>
    </>
  );
}
