import { t } from '@lingui/core/macro';
import type { SpotlightActionData } from '@mantine/spotlight';
import {
  IconBarcode,
  IconLink,
  IconPlug,
  IconPointer,
  IconSettings,
  IconUserBolt,
  IconUserCog
} from '@tabler/icons-react';
import type { NavigateFunction } from 'react-router-dom';

import { ModelInformationDict } from '@lib/enums/ModelInformation';
import { UserRoles } from '@lib/index';
import { openContextModal } from '@mantine/modals';
import { useMemo } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { useLocalState } from '../states/LocalState';
import { useGlobalSettingsState } from '../states/SettingsStates';
import { useUserState } from '../states/UserState';
import { aboutInvenTree, docLinks, licenseInfo, serverInfo } from './links';

export function openQrModal(navigate: NavigateFunction) {
  return openContextModal({
    modal: 'qr',
    innerProps: { navigate: navigate }
  });
}

export function getActions(navigate: NavigateFunction) {
  const setNavigationOpen = useLocalState(
    useShallow((state) => state.setNavigationOpen)
  );
  const globalSettings = useGlobalSettingsState();
  const user = useUserState();

  const actions: SpotlightActionData[] = useMemo(() => {
    const _actions: SpotlightActionData[] = [
      {
        id: 'dashboard',
        label: t`Dashboard`,
        description: t`Go to the InvenTree dashboard`,
        onClick: () => navigate('/'),
        leftSection: <IconLink size='1.2rem' />
      },
      {
        id: 'documentation',
        label: t`Documentation`,
        description: t`Visit the documentation to learn more about InvenTree`,
        onClick: () => {
          window.location.href = docLinks.faq;
        },
        leftSection: <IconLink size='1.2rem' />
      },
      {
        id: 'about',
        label: t`About InvenTree`,
        description: t`About the InvenTree org`,
        onClick: () => aboutInvenTree(),
        leftSection: <IconLink size='1.2rem' />
      },
      {
        id: 'server-info',
        label: t`Server Information`,
        description: t`About this InvenTree instance`,
        onClick: () => serverInfo(),
        leftSection: <IconLink size='1.2rem' />
      },
      {
        id: 'license-info',
        label: t`License Information`,
        description: t`Licenses for dependencies of the service`,
        onClick: () => licenseInfo(),
        leftSection: <IconLink size='1.2rem' />
      },
      {
        id: 'navigation',
        label: t`Open Navigation`,
        description: t`Open the main navigation menu`,
        onClick: () => setNavigationOpen(true),
        leftSection: <IconPointer size='1.2rem' />
      },
      {
        id: 'scan',
        label: t`Scan`,
        description: t`Scan a barcode or QR code`,
        onClick: () => openQrModal(navigate),
        leftSection: <IconBarcode size='1.2rem' />
      },
      {
        id: 'user-settings',
        label: t`User Settings`,

        description: t`Go to your user settings`,
        onClick: () => navigate('/settings/user'),
        leftSection: <IconUserCog size='1.2rem' />
      }
    ];

    // Page Actions
    user?.hasViewRole(UserRoles.purchase_order) &&
      _actions.push({
        id: 'purchase-orders',
        label: t`Purchase Orders`,
        description: t`Go to Purchase Orders`,
        onClick: () =>
          navigate(ModelInformationDict['purchaseorder'].url_overview!),
        leftSection: <IconLink size='1.2rem' />
      });

    user?.hasViewRole(UserRoles.sales_order) &&
      _actions.push({
        id: 'sales-orders',
        label: t`Sales Orders`,
        description: t`Go to Sales Orders`,
        onClick: () =>
          navigate(ModelInformationDict['salesorder'].url_overview!),
        leftSection: <IconLink size='1.2rem' />
      });

    globalSettings.isSet('RETURNORDER_ENABLED') &&
      user?.hasViewRole(UserRoles.return_order) &&
      _actions.push({
        id: 'return-orders',
        label: t`Return Orders`,
        description: t`Go to Return Orders`,
        onClick: () =>
          navigate(ModelInformationDict['returnorder'].url_overview!),
        leftSection: <IconLink size='1.2rem' />
      });

    user?.hasViewRole(UserRoles.build) &&
      _actions.push({
        id: 'builds',
        label: t`Build Orders`,
        description: t`Go to Build Orders`,
        onClick: () => navigate(ModelInformationDict['build'].url_overview!),
        leftSection: <IconLink size='1.2rem' />
      });

    user?.isStaff() &&
      _actions.push({
        id: 'system-settings',
        label: t`System Settings`,
        description: t`Go to System Settings`,
        onClick: () => navigate('/settings/system'),
        leftSection: <IconSettings size='1.2rem' />
      });

    user?.isStaff() &&
      _actions.push({
        id: 'admin-center',
        label: t`Admin Center`,
        description: t`Go to the Admin Center`,
        onClick: () => navigate('/settings/admin'),
        leftSection: <IconUserBolt size='1.2rem' />
      });

    user?.isStaff() &&
      _actions.push({
        id: 'plugin-settings',
        label: t`Plugins`,
        description: t`Manage InvenTree plugins`,
        onClick: () => navigate('/settings/admin/plugin'),
        leftSection: <IconPlug size='1.2rem' />
      });

    return _actions;
  }, [navigate, setNavigationOpen, globalSettings, user]);

  return actions;
}
