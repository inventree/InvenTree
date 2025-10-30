import { t } from '@lingui/core/macro';
import type { SpotlightActionData } from '@mantine/spotlight';
import {
  IconBarcode,
  IconLink,
  IconPointer,
  IconSettings,
  IconUserBolt,
  IconUserCog
} from '@tabler/icons-react';
import type { NavigateFunction } from 'react-router-dom';

import { openContextModal } from '@mantine/modals';
import { useShallow } from 'zustand/react/shallow';
import { useLocalState } from '../states/LocalState';
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
  const { user } = useUserState();

  const actions: SpotlightActionData[] = [
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

  // Staff actions

  user?.is_staff &&
    actions.push({
      id: 'system-settings',
      label: t`System Settings`,
      description: t`Go to System Settings`,
      onClick: () => navigate('/settings/system'),
      leftSection: <IconSettings size='1.2rem' />
    });

  user?.is_staff &&
    actions.push({
      id: 'admin-center',
      label: t`Admin Center`,
      description: t`Go to the Admin Center`,
      onClick: () => {}, /// navigate(menuItems['settings-admin'].link),}
      leftSection: <IconUserBolt size='1.2rem' />
    });

  return actions;
}
