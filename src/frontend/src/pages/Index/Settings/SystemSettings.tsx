import { t } from '@lingui/core/macro';
import { Skeleton, Stack } from '@mantine/core';
import {
  IconBellCog,
  IconCategory,
  IconClipboardList,
  IconCurrencyDollar,
  IconFileAnalytics,
  IconFingerprint,
  IconList,
  IconPackages,
  IconPlugConnected,
  IconQrcode,
  IconServerCog,
  IconShoppingCart,
  IconTag,
  IconTools,
  IconTruckDelivery,
  IconTruckReturn
} from '@tabler/icons-react';
import { lazy, useMemo } from 'react';

import { useShallow } from 'zustand/react/shallow';
import PermissionDenied from '../../../components/errors/PermissionDenied';
import PageTitle from '../../../components/nav/PageTitle';
import { SettingsHeader } from '../../../components/nav/SettingsHeader';
import type { PanelType } from '../../../components/panels/Panel';
import { PanelGroup } from '../../../components/panels/PanelGroup';
import { GlobalSettingList } from '../../../components/settings/SettingList';
import { Loadable } from '../../../functions/loading';
import { useServerApiState } from '../../../states/ServerApiState';
import { useUserState } from '../../../states/UserState';

const PluginSettingsGroup = Loadable(
  lazy(() => import('./PluginSettingsGroup'))
);

/**
 * System settings page
 */
export default function SystemSettings() {
  const systemSettingsPanels: PanelType[] = useMemo(() => {
    return [
      {
        name: 'server',
        label: t`Server`,
        icon: <IconServerCog />,
        content: (
          <GlobalSettingList
            keys={[
              'INVENTREE_BASE_URL',
              'INVENTREE_COMPANY_NAME',
              'INVENTREE_INSTANCE_ID',
              'INVENTREE_ANNOUNCE_ID',
              'INVENTREE_INSTANCE',
              'INVENTREE_INSTANCE_TITLE',
              'INVENTREE_RESTRICT_ABOUT',
              'DISPLAY_FULL_NAMES',
              'DISPLAY_PROFILE_INFO',
              'INVENTREE_UPDATE_CHECK_INTERVAL',
              'INVENTREE_DOWNLOAD_FROM_URL',
              'INVENTREE_DOWNLOAD_IMAGE_MAX_SIZE',
              'INVENTREE_DOWNLOAD_FROM_URL_USER_AGENT',
              'INVENTREE_STRICT_URLS',
              'INVENTREE_BACKUP_ENABLE',
              'INVENTREE_BACKUP_DAYS',
              'INVENTREE_DELETE_TASKS_DAYS',
              'INVENTREE_DELETE_ERRORS_DAYS',
              'INVENTREE_DELETE_NOTIFICATIONS_DAYS',
              'INVENTREE_DELETE_EMAIL_DAYS',
              'INVENTREE_PROTECT_EMAIL_LOG'
            ]}
          />
        )
      },
      {
        name: 'authentication',
        label: t`Authentication`,
        icon: <IconFingerprint />,
        content: (
          <GlobalSettingList
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
              'LOGIN_SIGNUP_SSO_AUTO',
              'LOGIN_ENABLE_SSO_GROUP_SYNC',
              'SSO_GROUP_MAP',
              'SSO_GROUP_KEY',
              'SSO_REMOVE_GROUPS'
            ]}
          />
        )
      },
      {
        name: 'barcode',
        label: t`Barcodes`,
        icon: <IconQrcode />,
        content: (
          <GlobalSettingList
            keys={[
              'BARCODE_ENABLE',
              'BARCODE_INPUT_DELAY',
              'BARCODE_WEBCAM_SUPPORT',
              'BARCODE_SHOW_TEXT',
              'BARCODE_GENERATION_PLUGIN',
              'BARCODE_STORE_RESULTS',
              'BARCODE_RESULTS_MAX_NUM'
            ]}
          />
        )
      },
      {
        name: 'notifications',
        label: t`Notifications`,
        icon: <IconBellCog />,
        content: (
          <PluginSettingsGroup
            mixin='notification'
            global={true}
            message={t`The settings below are specific to each available notification method`}
          />
        )
      },
      {
        name: 'pricing',
        label: t`Pricing`,
        icon: <IconCurrencyDollar />,
        content: (
          <>
            <GlobalSettingList
              keys={[
                'INVENTREE_DEFAULT_CURRENCY',
                'CURRENCY_CODES',
                'PART_INTERNAL_PRICE',
                'PART_BOM_USE_INTERNAL_PRICE',
                'PRICING_DECIMAL_PLACES_MIN',
                'PRICING_DECIMAL_PLACES',
                'PRICING_AUTO_UPDATE',
                'PRICING_UPDATE_DAYS'
              ]}
            />
            <br />
            <GlobalSettingList
              keys={[
                'PRICING_USE_SUPPLIER_PRICING',
                'PRICING_PURCHASE_HISTORY_OVERRIDES_SUPPLIER',
                'PRICING_USE_STOCK_PRICING',
                'PRICING_STOCK_ITEM_AGE_DAYS',
                'PRICING_USE_VARIANT_PRICING',
                'PRICING_ACTIVE_VARIANTS'
              ]}
            />
            <br />
            <GlobalSettingList
              keys={['CURRENCY_UPDATE_PLUGIN', 'CURRENCY_UPDATE_INTERVAL']}
            />
          </>
        )
      },
      {
        name: 'labels',
        label: t`Labels`,
        icon: <IconTag />,
        content: <GlobalSettingList keys={['LABEL_ENABLE', 'LABEL_DPI']} />
      },
      {
        name: 'reporting',
        label: t`Reporting`,
        icon: <IconFileAnalytics />,
        content: (
          <GlobalSettingList
            keys={[
              'REPORT_ENABLE',
              'REPORT_DEFAULT_PAGE_SIZE',
              'REPORT_DEBUG_MODE',
              'REPORT_LOG_ERRORS'
            ]}
          />
        )
      },
      {
        name: 'parameters',
        label: t`Parameters`,
        icon: <IconList />,
        content: <GlobalSettingList keys={['PARAMETER_ENFORCE_UNITS']} />
      },
      {
        name: 'parts',
        label: t`Parts`,
        icon: <IconCategory />,
        content: (
          <GlobalSettingList
            keys={[
              'PART_IPN_REGEX',
              'PART_ALLOW_DUPLICATE_IPN',
              'PART_ALLOW_EDIT_IPN',
              'PART_ALLOW_DELETE_FROM_ASSEMBLY',
              'PART_ENABLE_REVISION',
              'PART_REVISION_ASSEMBLY_ONLY',
              'PART_NAME_FORMAT',
              'PART_SHOW_RELATED',
              'PART_CREATE_INITIAL',
              'PART_CREATE_SUPPLIER',
              'PART_TEMPLATE',
              'PART_ASSEMBLY',
              'PART_COMPONENT',
              'PART_TRACKABLE',
              'PART_PURCHASEABLE',
              'PART_SALABLE',
              'PART_VIRTUAL',
              'PART_COPY_BOM',
              'PART_COPY_PARAMETERS',
              'PART_COPY_TESTS',
              'PART_CATEGORY_PARAMETERS',
              'PART_CATEGORY_DEFAULT_ICON'
            ]}
          />
        )
      },
      {
        name: 'stock',
        label: t`Stock`,
        icon: <IconPackages />,
        content: (
          <GlobalSettingList
            keys={[
              'SERIAL_NUMBER_GLOBALLY_UNIQUE',
              'STOCK_DELETE_DEPLETED_DEFAULT',
              'STOCK_BATCH_CODE_TEMPLATE',
              'STOCK_ENABLE_EXPIRY',
              'STOCK_STALE_DAYS',
              'STOCK_ALLOW_EXPIRED_SALE',
              'STOCK_ALLOW_EXPIRED_BUILD',
              'STOCK_OWNERSHIP_CONTROL',
              'STOCK_LOCATION_DEFAULT_ICON',
              'STOCK_SHOW_INSTALLED_ITEMS',
              'STOCK_ENFORCE_BOM_INSTALLATION',
              'STOCK_ALLOW_OUT_OF_STOCK_TRANSFER',
              'TEST_STATION_DATA'
            ]}
          />
        )
      },
      {
        name: 'stock-history',
        label: t`Stock History`,
        icon: <IconClipboardList />,
        content: (
          <GlobalSettingList
            keys={[
              'STOCKTAKE_ENABLE',
              'STOCKTAKE_EXCLUDE_EXTERNAL',
              'STOCKTAKE_AUTO_DAYS',
              'STOCKTAKE_DELETE_OLD_ENTRIES',
              'STOCKTAKE_DELETE_DAYS'
            ]}
          />
        )
      },
      {
        name: 'buildorders',
        label: t`Build Orders`,
        icon: <IconTools />,
        content: (
          <GlobalSettingList
            keys={[
              'BUILDORDER_REFERENCE_PATTERN',
              'BUILDORDER_EXTERNAL_BUILDS',
              'BUILDORDER_REQUIRE_RESPONSIBLE',
              'BUILDORDER_REQUIRE_ACTIVE_PART',
              'BUILDORDER_REQUIRE_LOCKED_PART',
              'BUILDORDER_REQUIRE_VALID_BOM',
              'BUILDORDER_REQUIRE_CLOSED_CHILDS',
              'PREVENT_BUILD_COMPLETION_HAVING_INCOMPLETED_TESTS'
            ]}
          />
        )
      },
      {
        name: 'purchaseorders',
        label: t`Purchase Orders`,
        icon: <IconShoppingCart />,
        content: (
          <GlobalSettingList
            keys={[
              'PURCHASEORDER_REFERENCE_PATTERN',
              'PURCHASEORDER_REQUIRE_RESPONSIBLE',
              'PURCHASEORDER_CONVERT_CURRENCY',
              'PURCHASEORDER_EDIT_COMPLETED_ORDERS',
              'PURCHASEORDER_AUTO_COMPLETE'
            ]}
          />
        )
      },
      {
        name: 'salesorders',
        label: t`Sales Orders`,
        icon: <IconTruckDelivery />,
        content: (
          <GlobalSettingList
            keys={[
              'SALESORDER_REFERENCE_PATTERN',
              'SALESORDER_REQUIRE_RESPONSIBLE',
              'SALESORDER_DEFAULT_SHIPMENT',
              'SALESORDER_EDIT_COMPLETED_ORDERS',
              'SALESORDER_SHIP_COMPLETE',
              'SALESORDER_SHIPMENT_REQUIRES_CHECK'
            ]}
          />
        )
      },
      {
        name: 'returnorders',
        label: t`Return Orders`,
        icon: <IconTruckReturn />,
        content: (
          <GlobalSettingList
            keys={[
              'RETURNORDER_ENABLED',
              'RETURNORDER_REFERENCE_PATTERN',
              'RETURNORDER_REQUIRE_RESPONSIBLE',
              'RETURNORDER_EDIT_COMPLETED_ORDERS'
            ]}
          />
        )
      },
      {
        name: 'plugins',
        label: t`Plugin Settings`,
        icon: <IconPlugConnected />,
        content: <PluginSettingsGroup global={true} />
      }
    ];
  }, []);

  const user = useUserState();

  const [server] = useServerApiState(useShallow((state) => [state.server]));

  if (!user.isLoggedIn()) {
    return <Skeleton />;
  }

  return (
    <>
      <PageTitle title={t`System Settings`} />
      {user.isStaff() ? (
        <Stack gap='xs'>
          <SettingsHeader
            label='system'
            title={t`System Settings`}
            subtitle={server.instance || ''}
          />
          <PanelGroup
            pageKey='system-settings'
            panels={systemSettingsPanels}
            model='systemsettings'
            id={null}
          />
        </Stack>
      ) : (
        <PermissionDenied />
      )}
    </>
  );
}
